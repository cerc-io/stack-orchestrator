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

import sys

import click
import yaml

from stack_orchestrator.deploy.webapp.util import (LaconicRegistryClient)


def fatal(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(1)


@click.command()
@click.option(
    "--laconic-config", help="Provide a config file for laconicd", required=True
)
@click.option(
    "--deployer",
    help="The LRN of the deployer to process this request.",
    required=True
)
@click.option(
    "--deployment",
    help="Deployment record (ApplicationDeploymentRecord) id of the deployment to remove.",
    required=True,
)
@click.option(
    "--make-payment",
    help="The payment to make (in alnt).  The value should be a number or 'auto' to use the deployer's minimum required payment.",
)
@click.option(
    "--use-payment", help="The TX id of an existing, unused payment", default=None
)
@click.option(
    "--dry-run",
    help="Don't publish anything, just report what would be done.",
    is_flag=True,
)
@click.pass_context
def command(
    ctx,
    laconic_config,
    deployer,
    deployment,
    make_payment,
    use_payment,
    dry_run,
):
    if make_payment and use_payment:
        fatal("Cannot use --make-payment and --use-payment at the same time.")

    laconic = LaconicRegistryClient(laconic_config)

    deployer_record = laconic.get_record(deployer)
    if not deployer_record:
        fatal(f"Unable to locate deployer: {deployer}")

    undeployment_request = {
        "record": {
            "type": "ApplicationDeploymentRemovalRequest",
            "version": "1.0.0",
            "deployer": deployer,
            "deployment": deployment,
        }
    }

    if make_payment:
        amount = 0
        if dry_run:
            undeployment_request["record"]["payment"] = "DRY_RUN"
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
            undeployment_request["record"]["payment"] = receipt.tx.hash
            print("Payment TX:", receipt.tx.hash)
    elif use_payment:
        undeployment_request["record"]["payment"] = use_payment

    if dry_run:
        print(yaml.dump(undeployment_request))
        return

    laconic.publish(undeployment_request)
