# Copyright ©2023 Vulcanize
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http:#www.gnu.org/licenses/>.

import shutil
import sys
import tempfile
from datetime import datetime
import base64

import gnupg
import click
import requests
import yaml

from stack_orchestrator.deploy.webapp.util import (
    AUCTION_KIND_PROVIDER,
    AuctionStatus,
    LaconicRegistryClient,
)
from dotenv import dotenv_values


def fatal(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(1)


@click.command()
@click.option(
    "--laconic-config", help="Provide a config file for laconicd", required=True
)
@click.option(
    "--app",
    help="The LRN of the application to deploy.",
    required=True,
)
@click.option(
    "--auction-id",
    help="Deployment auction id. Can be used instead of deployer and payment.",
)
@click.option(
    "--deployer",
    help="The LRN of the deployer to process this request.",
)
@click.option("--env-file", help="environment file for webapp")
@click.option("--config-ref", help="The ref of an existing config upload to use.")
@click.option(
    "--make-payment",
    help="The payment to make (in alnt).  The value should be a number or 'auto' to use the deployer's minimum required payment.",
)
@click.option(
    "--use-payment", help="The TX id of an existing, unused payment", default=None
)
@click.option("--dns", help="the DNS name to request (default is autogenerated)")
@click.option(
    "--dry-run",
    help="Don't publish anything, just report what would be done.",
    is_flag=True,
)
@click.pass_context
def command(  # noqa: C901
    ctx,
    laconic_config,
    app,
    auction_id,
    deployer,
    env_file,
    config_ref,
    make_payment,
    use_payment,
    dns,
    dry_run,
):
    if auction_id and deployer:
        print("Cannot specify both --auction-id and --deployer", file=sys.stderr)
        sys.exit(2)

    if not auction_id and not deployer:
        print("Must specify either --auction-id or --deployer", file=sys.stderr)
        sys.exit(2)

    if auction_id and (make_payment or use_payment):
        print("Cannot specify --auction-id with --make-payment or --use-payment", file=sys.stderr)
        sys.exit(2)

    if env_file and config_ref:
        fatal("Cannot use --env-file and --config-ref at the same time.")

    laconic = LaconicRegistryClient(laconic_config)

    app_record = laconic.get_record(app)
    if not app_record:
        fatal(f"Unable to locate app: {app}")

    # Deployers to send requests to
    deployer_records = []

    auction = None
    auction_winners = None
    if auction_id:
        # Fetch auction record for given auction
        auction_records_by_id = laconic.app_deployment_auctions({"auction": auction_id})
        if len(auction_records_by_id) == 0:
            fatal(f"Unable to locate record for auction: {auction_id}")

        # Cross check app against application in the auction record
        auction_app = auction_records_by_id[0].attributes.application
        if auction_app != app:
            fatal(f"Requested application {app} does not match application from auction record {auction_app}")

        # Fetch auction details
        auction = laconic.get_auction(auction_id)
        if not auction:
            fatal(f"Unable to locate auction: {auction_id}")

        # Check auction owner
        if auction.ownerAddress != laconic.whoami().address:
            fatal(f"Auction {auction_id} owner mismatch")

        # Check auction kind
        if auction.kind != AUCTION_KIND_PROVIDER:
            fatal(f"Auction kind needs to be ${AUCTION_KIND_PROVIDER}, got {auction.kind}")

        # Check auction status
        if auction.status != AuctionStatus.COMPLETED:
            fatal(f"Auction {auction_id} not completed yet, status {auction.status}")

        # Check that winner list is not empty
        if len(auction.winnerAddresses) == 0:
            fatal(f"Auction {auction_id} has no winners")

        auction_winners = auction.winnerAddresses

        # Get deployer record for all the auction winners
        for auction_winner in auction_winners:
            # TODO: Match auction winner address with provider address?
            deployer_records_by_owner = laconic.webapp_deployers({"paymentAddress": auction_winner})
            if len(deployer_records_by_owner) == 0:
                print(f"WARNING: Unable to locate deployer for auction winner {auction_winner}")

            # Take first record with name set
            target_deployer_record = deployer_records_by_owner[0]
            for r in deployer_records_by_owner:
                if len(r.names) > 0:
                    target_deployer_record = r
                    break
            deployer_records.append(target_deployer_record)
    else:
        deployer_record = laconic.get_record(deployer)
        if not deployer_record:
            fatal(f"Unable to locate deployer: {deployer}")

        deployer_records.append(deployer_record)

    # Create and send request to each deployer
    deployment_requests = []
    for deployer_record in deployer_records:
        # Upload config to deployers if env_file is passed
        if env_file:
            tempdir = tempfile.mkdtemp()
            try:
                gpg = gnupg.GPG(gnupghome=tempdir)

                # Import the deployer's public key
                result = gpg.import_keys(
                    base64.b64decode(deployer_record.attributes.publicKey)
                )
                if 1 != result.imported:
                    fatal("Failed to import deployer's public key.")

                recip = gpg.list_keys()[0]["uids"][0]

                # Wrap the config
                config = {
                    # Include account (and payment?) details
                    "authorized": [laconic.whoami().address],
                    "config": {"env": dict(dotenv_values(env_file))},
                }
                serialized = yaml.dump(config)

                # Encrypt
                result = gpg.encrypt(serialized, recip, always_trust=True, armor=False)
                if not result.ok:
                    fatal("Failed to encrypt config.")

                # Upload it to the deployer's API
                response = requests.post(
                    f"{deployer_record.attributes.apiUrl}/upload/config",
                    data=result.data,
                    headers={"Content-Type": "application/octet-stream"},
                )
                if not response.ok:
                    response.raise_for_status()

                config_ref = response.json()["id"]
            finally:
                shutil.rmtree(tempdir, ignore_errors=True)

        target_deployer = deployer
        if (not deployer) and len(deployer_record.names):
            target_deployer = deployer_record.names[0]

        deployment_request = {
            "record": {
                "type": "ApplicationDeploymentRequest",
                "application": app,
                "version": "1.0.0",
                "name": f"{app_record.attributes.name}@{app_record.attributes.version}",
                "deployer": target_deployer,
                "meta": {"when": str(datetime.utcnow())},
            }
        }

        if auction_id:
            deployment_request["record"]["auction"] = auction_id

        if config_ref:
            deployment_request["record"]["config"] = {"ref": config_ref}

        if dns:
            deployment_request["record"]["dns"] = dns.lower()

        if make_payment:
            amount = 0
            if dry_run:
                deployment_request["record"]["payment"] = "DRY_RUN"
            elif "auto" == make_payment:
                if "minimumPayment" in deployer_record.attributes:
                    amount = int(
                        deployer_record.attributes.minimumPayment.replace("alnt", "")
                    )
            else:
                amount = make_payment
            if amount:
                receipt = laconic.send_tokens(
                    deployer_record.attributes.paymentAddress, amount
                )
                deployment_request["record"]["payment"] = receipt.tx.hash
                print("Payment TX:", receipt.tx.hash)
        elif use_payment:
            deployment_request["record"]["payment"] = use_payment

        deployment_requests.append(deployment_request)

    # Send all requests
    for deployment_request in deployment_requests:
        if dry_run:
            print(yaml.dump(deployment_request))
            continue

        laconic.publish(deployment_request)
