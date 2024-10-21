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
import json

import click

from stack_orchestrator.deploy.webapp.util import (
    AttrDict,
    LaconicRegistryClient,
    TimedLogger,
    load_known_requests,
    AUCTION_KIND_PROVIDER,
    AuctionStatus,
)


def process_app_deployment_auction(
    ctx,
    laconic: LaconicRegistryClient,
    request,
    current_status,
    reveal_file_path,
    bid_amount,
    logger,
):
    # Fetch auction details
    auction_id = request.attributes.auction
    auction = laconic.get_auction(auction_id)
    if not auction:
        raise Exception(f"Unable to locate auction: {auction_id}")

    # Check auction kind
    if auction.kind != AUCTION_KIND_PROVIDER:
        raise Exception(f"Auction kind needs to be ${AUCTION_KIND_PROVIDER}, got {auction.kind}")

    if current_status == "PENDING":
        # Skip if pending auction not in commit state
        if auction.status != AuctionStatus.COMMIT:
            logger.log(f"Skipping pending request, auction {auction_id} status: {auction.status}")
            return "SKIP", ""

        # Check max_price
        bid_amount_int = int(bid_amount)
        max_price_int = int(auction.maxPrice.quantity)
        if max_price_int < bid_amount_int:
            logger.log(f"Skipping auction {auction_id} with max_price ({max_price_int}) less than bid_amount ({bid_amount_int})")
            return "SKIP", ""

        # Bid on the auction
        reveal_file_path = laconic.commit_bid(auction_id, bid_amount_int)
        logger.log(f"Commited bid on auction {auction_id} with amount {bid_amount_int}")

        return "COMMIT", reveal_file_path

    if current_status == "COMMIT":
        # Return if auction still in commit state
        if auction.status == AuctionStatus.COMMIT:
            logger.log(f"Auction {auction_id} status: {auction.status}")
            return current_status, reveal_file_path

        # Reveal bid
        if auction.status == AuctionStatus.REVEAL:
            laconic.reveal_bid(auction_id, reveal_file_path)
            logger.log(f"Revealed bid on auction {auction_id}")

            return "REVEAL", reveal_file_path

        raise Exception(f"Unexpected auction {auction_id} status: {auction.status}")

    if current_status == "REVEAL":
        # Return if auction still in reveal state
        if auction.status == AuctionStatus.REVEAL:
            logger.log(f"Auction {auction_id} status: {auction.status}")
            return current_status, reveal_file_path

        # Return if auction is completed
        if auction.status == AuctionStatus.COMPLETED:
            logger.log(f"Auction {auction_id} completed")
            return "COMPLETED", ""

        raise Exception(f"Unexpected auction {auction_id} status: {auction.status}")

    raise Exception(f"Got request with unexpected status: {current_status}")


def dump_known_auction_requests(filename, requests, status="SEEN"):
    if not filename:
        return
    known_requests = load_known_requests(filename)
    for r in requests:
        known_requests[r.id] = {"revealFile": r.revealFile, "status": status}
    with open(filename, "w") as f:
        json.dump(known_requests, f)


@click.command()
@click.option(
    "--laconic-config", help="Provide a config file for laconicd", required=True
)
@click.option(
    "--state-file",
    help="File to store state about previously seen auction requests.",
    required=True,
)
@click.option(
    "--bid-amount",
    help="Bid to place on application deployment auctions (in alnt)",
    required=True,
)
@click.option(
    "--dry-run", help="Don't do anything, just report what would be done.", is_flag=True
)
@click.pass_context
def command(
    ctx,
    laconic_config,
    state_file,
    bid_amount,
    dry_run,
):
    if int(bid_amount) < 0:
        print("--bid-amount cannot be less than 0", file=sys.stderr)
        sys.exit(2)

    logger = TimedLogger(file=sys.stderr)

    try:
        laconic = LaconicRegistryClient(laconic_config, log_file=sys.stderr)
        auctions_requests = laconic.app_deployment_auctions()

        previous_requests = {}
        logger.log(f"Loading known auctions from {state_file}...")
        previous_requests = load_known_requests(state_file)

        # Process new requests first
        auctions_requests.sort(key=lambda r: r.createTime)
        auctions_requests.reverse()

        requests_to_execute = []

        for r in auctions_requests:
            logger.log(f"BEGIN: Examining request {r.id}")
            result_status = "PENDING"
            reveal_file_path = ""
            try:
                application = r.attributes.application

                # Handle already seen requests
                if r.id in previous_requests:
                    # If it's not in commit or reveal status, skip the request as we've already seen it
                    current_status = previous_requests[r.id].get("status", "")
                    result_status = current_status
                    if current_status not in ["COMMIT", "REVEAL"]:
                        logger.log(f"Skipping request {r.id}, we've already seen it.")
                        continue

                    reveal_file_path = previous_requests[r.id].get("revealFile", "")
                    logger.log(f"Found existing auction request {r.id} for application {application}, status {current_status}.")
                else:
                    # It's a fresh request, check application record
                    app = laconic.get_record(application)
                    if not app:
                        logger.log(f"Skipping request {r.id}, cannot locate app.")
                        result_status = "ERROR"
                        continue

                    logger.log(f"Found pending auction request {r.id} for application {application}.")

                # Add requests to be processed
                requests_to_execute.append((r, result_status, reveal_file_path))

            except Exception as e:
                result_status = "ERROR"
                logger.log(f"ERROR: examining request {r.id}: " + str(e))
            finally:
                logger.log(f"DONE: Examining request {r.id} with result {result_status}.")
                if result_status in ["ERROR"]:
                    dump_known_auction_requests(state_file, [AttrDict({"id": r.id, "revealFile": reveal_file_path})], result_status)

        logger.log(f"Found {len(requests_to_execute)} request(s) to process.")

        if not dry_run:
            for r, current_status, reveal_file_path in requests_to_execute:
                logger.log(f"Processing {r.id}: BEGIN")
                result_status = "ERROR"
                try:
                    result_status, reveal_file_path = process_app_deployment_auction(
                        ctx,
                        laconic,
                        r,
                        current_status,
                        reveal_file_path,
                        bid_amount,
                        logger,
                    )
                except Exception as e:
                    logger.log(f"ERROR {r.id}:" + str(e))
                finally:
                    logger.log(f"Processing {r.id}: END - {result_status}")
                    dump_known_auction_requests(state_file, [AttrDict({"id": r.id, "revealFile": reveal_file_path})], result_status)
    except Exception as e:
        logger.log("UNCAUGHT ERROR:" + str(e))
        raise e
