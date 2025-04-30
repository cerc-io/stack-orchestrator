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

import base64
import click
import sys
import yaml

from urllib.parse import urlparse

from stack_orchestrator.deploy.webapp.util import LaconicRegistryClient


@click.command()
@click.option(
    "--laconic-config", help="Provide a config file for laconicd", required=True
)
@click.option("--api-url", help="The API URL of the deployer.", required=True)
@click.option(
    "--public-key-file",
    help="The public key to use.  This should be a binary file.",
    required=True,
)
@click.option(
    "--lrn", help="eg, lrn://laconic/deployers/my.deployer.name", required=True
)
@click.option(
    "--payment-address",
    help="The address to which payments should be made.  "
    "Default is the current laconic account.",
    default=None,
)
@click.option(
    "--min-required-payment",
    help="List the minimum required payment (in alnt) to process a deployment request.",
    default=0,
)
@click.option(
    "--atom-payment-address",
    help="The Cosmos ATOM address to which payments should be made.",
    default=None,
)
@click.option(
    "--min-atom-payment",
    help="List the minimum required payment (in ATOM) to process a deployment request.",
    default=1,
    type=float,
)
@click.option(
    "--dry-run",
    help="Don't publish anything, just report what would be done.",
    is_flag=True,
)
@click.pass_context
def command(  # noqa: C901
    ctx,
    laconic_config,
    api_url,
    public_key_file,
    lrn,
    payment_address,
    min_required_payment,
    atom_payment_address,
    min_atom_payment,
    dry_run,
):
    laconic = LaconicRegistryClient(laconic_config)
    if not payment_address:
        payment_address = laconic.whoami().address

    pub_key = base64.b64encode(open(public_key_file, "rb").read()).decode("ASCII")
    hostname = urlparse(api_url).hostname
    webapp_deployer_record = {
        "record": {
            "type": "WebappDeployer",
            "version": "1.0.0",
            "apiUrl": api_url,
            "name": hostname,
            "publicKey": pub_key,
            "paymentAddress": payment_address,
        }
    }

    if min_required_payment:
        webapp_deployer_record["record"][
            "minimumPayment"
        ] = f"{min_required_payment}alnt"
        
    if atom_payment_address:
        webapp_deployer_record["record"]["atomPaymentAddress"] = atom_payment_address
        webapp_deployer_record["record"]["minimumAtomPayment"] = min_atom_payment

    if dry_run:
        yaml.dump(webapp_deployer_record, sys.stdout)
        return

    laconic.publish(webapp_deployer_record, [lrn])
