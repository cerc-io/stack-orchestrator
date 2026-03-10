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

from stack_orchestrator.deploy.webapp.util import (
    AUCTION_KIND_PROVIDER,
    TOKEN_DENOM,
    LaconicRegistryClient,
)


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
    "--commits-duration",
    help="Auction commits duration (in seconds) (default: 600).",
    default=600,
)
@click.option(
    "--reveals-duration",
    help="Auction reveals duration (in seconds) (default: 600).",
    default=600,
)
@click.option(
    "--commit-fee",
    help="Auction bid commit fee (in alnt) (default: 100000).",
    default=100000,
)
@click.option(
    "--reveal-fee",
    help="Auction bid reveal fee (in alnt) (default: 100000).",
    default=100000,
)
@click.option(
    "--max-price",
    help="Max acceptable bid price (in alnt).",
    required=True,
)
@click.option(
    "--num-providers",
    help="Max acceptable bid price (in alnt).",
    required=True,
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
    app,
    commits_duration,
    reveals_duration,
    commit_fee,
    reveal_fee,
    max_price,
    num_providers,
    dry_run,
):
    laconic = LaconicRegistryClient(laconic_config)

    app_record = laconic.get_record(app)
    if not app_record:
        fatal(f"Unable to locate app: {app}")

    provider_auction_params = {
        "kind": AUCTION_KIND_PROVIDER,
        "commits_duration": commits_duration,
        "reveals_duration": reveals_duration,
        "denom": TOKEN_DENOM,
        "commit_fee": commit_fee,
        "reveal_fee": reveal_fee,
        "max_price": max_price,
        "num_providers": num_providers,
    }
    auction_id = laconic.create_deployment_auction(provider_auction_params)
    print("Deployment auction created:", auction_id)

    if not auction_id:
        fatal("Unable to create a provider auction")

    deployment_auction = {
        "record": {
            "type": "ApplicationDeploymentAuction",
            "application": app,
            "auction": auction_id,
        }
    }

    if dry_run:
        print(yaml.dump(deployment_auction))
        return

    # Publish the deployment auction record
    laconic.publish(deployment_auction)
