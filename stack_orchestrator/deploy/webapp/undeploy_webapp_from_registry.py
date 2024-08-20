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

import json
import os
import shutil
import subprocess
import sys

import click

from stack_orchestrator.deploy.webapp.util import (
    TimedLogger,
    LaconicRegistryClient,
    match_owner,
    skip_by_tag,
    confirm_payment,
)

main_logger = TimedLogger(file=sys.stderr)


def process_app_removal_request(
    ctx,
    laconic: LaconicRegistryClient,
    app_removal_request,
    deployment_parent_dir,
    delete_volumes,
    delete_names,
):
    deployment_record = laconic.get_record(
        app_removal_request.attributes.deployment, require=True
    )
    dns_record = laconic.get_record(deployment_record.attributes.dns, require=True)
    deployment_dir = os.path.join(
        deployment_parent_dir, dns_record.attributes.name.lower()
    )

    if not os.path.exists(deployment_dir):
        raise Exception("Deployment directory %s does not exist." % deployment_dir)

    # Check if the removal request is from the owner of the DnsRecord or deployment record.
    matched_owner = match_owner(app_removal_request, deployment_record, dns_record)

    # Or of the original deployment request.
    if not matched_owner and deployment_record.attributes.request:
        matched_owner = match_owner(
            app_removal_request,
            laconic.get_record(deployment_record.attributes.request, require=True),
        )

    if matched_owner:
        main_logger.log("Matched deployment ownership:", matched_owner)
    else:
        raise Exception(
            "Unable to confirm ownership of deployment %s for removal request %s"
            % (deployment_record.id, app_removal_request.id)
        )

    # TODO(telackey): Call the function directly.  The easiest way to build the correct click context is to
    # exec the process, but it would be better to refactor so we could just call down_operation with the
    # necessary parameters
    down_command = [sys.argv[0], "deployment", "--dir", deployment_dir, "down"]
    if delete_volumes:
        down_command.append("--delete-volumes")
    result = subprocess.run(down_command)
    result.check_returncode()

    removal_record = {
        "record": {
            "type": "ApplicationDeploymentRemovalRecord",
            "version": "1.0.0",
            "request": app_removal_request.id,
            "deployment": deployment_record.id,
        }
    }
    laconic.publish(removal_record)

    if delete_names:
        if deployment_record.names:
            for name in deployment_record.names:
                laconic.delete_name(name)

        if dns_record.names:
            for name in dns_record.names:
                laconic.delete_name(name)

    if delete_volumes:
        shutil.rmtree(deployment_dir)


def load_known_requests(filename):
    if filename and os.path.exists(filename):
        return json.load(open(filename, "r"))
    return {}


def dump_known_requests(filename, requests):
    if not filename:
        return
    known_requests = load_known_requests(filename)
    for r in requests:
        known_requests[r.id] = r.createTime
    json.dump(known_requests, open(filename, "w"))


@click.command()
@click.option(
    "--laconic-config", help="Provide a config file for laconicd", required=True
)
@click.option(
    "--deployment-parent-dir",
    help="Create deployment directories beneath this directory",
    required=True,
)
@click.option("--request-id", help="The ApplicationDeploymentRemovalRequest to process")
@click.option(
    "--discover",
    help="Discover and process all pending ApplicationDeploymentRemovalRequests",
    is_flag=True,
    default=False,
)
@click.option(
    "--state-file", help="File to store state about previously seen requests."
)
@click.option(
    "--only-update-state",
    help="Only update the state file, don't process any requests anything.",
    is_flag=True,
)
@click.option(
    "--delete-names/--preserve-names",
    help="Delete all names associated with removed deployments.",
    default=True,
)
@click.option(
    "--delete-volumes/--preserve-volumes", default=True, help="delete data volumes"
)
@click.option(
    "--dry-run", help="Don't do anything, just report what would be done.", is_flag=True
)
@click.option(
    "--include-tags",
    help="Only include requests with matching tags (comma-separated).",
    default="",
)
@click.option(
    "--exclude-tags",
    help="Exclude requests with matching tags (comma-separated).",
    default="",
)
@click.option(
    "--min-required-payment",
    help="Requests must have a minimum payment to be processed",
    default=0,
)
@click.option(
    "--payment-address",
    help="The address to which payments should be made.  "
    "Default is the current laconic account.",
    default=None,
)
@click.option(
    "--all-requests",
    help="Handle requests addressed to anyone (by default only requests to"
    "my payment address are examined).",
    is_flag=True,
)
@click.pass_context
def command(  # noqa: C901
    ctx,
    laconic_config,
    deployment_parent_dir,
    request_id,
    discover,
    state_file,
    only_update_state,
    delete_names,
    delete_volumes,
    dry_run,
    include_tags,
    exclude_tags,
    min_required_payment,
    payment_address,
    all_requests,
):
    if request_id and discover:
        print("Cannot specify both --request-id and --discover", file=sys.stderr)
        sys.exit(2)

    if not request_id and not discover:
        print("Must specify either --request-id or --discover", file=sys.stderr)
        sys.exit(2)

    if only_update_state and not state_file:
        print("--only-update-state requires --state-file", file=sys.stderr)
        sys.exit(2)

    # Split CSV and clean up values.
    include_tags = [tag.strip() for tag in include_tags.split(",") if tag]
    exclude_tags = [tag.strip() for tag in exclude_tags.split(",") if tag]

    laconic = LaconicRegistryClient(laconic_config, log_file=sys.stderr)
    if not payment_address:
        payment_address = laconic.whoami().address

    # Find deployment removal requests.
    # single request
    if request_id:
        main_logger.log(f"Retrieving request {request_id}...")
        requests = [laconic.get_record(request_id, require=True)]
        # TODO: assert record type
    # all requests
    elif discover:
        main_logger.log("Discovering removal requests...")
        if all_requests:
            requests = laconic.app_deployment_removal_requests()
        else:
            requests = laconic.app_deployment_removal_requests({"to": payment_address})

    if only_update_state:
        if not dry_run:
            dump_known_requests(state_file, requests)
        return

    previous_requests = {}
    if state_file:
        main_logger.log(f"Loading known requests from {state_file}...")
        previous_requests = load_known_requests(state_file)

    requests.sort(key=lambda r: r.createTime)
    requests.reverse()

    # Find deployments.
    named_deployments = {}
    main_logger.log("Discovering app deployments...")
    for d in laconic.app_deployments(all=False):
        named_deployments[d.id] = d

    # Find removal requests.
    removals_by_deployment = {}
    removals_by_request = {}
    main_logger.log("Discovering deployment removals...")
    for r in laconic.app_deployment_removals():
        if r.attributes.deployment:
            # TODO: should we handle CRNs?
            removals_by_deployment[r.attributes.deployment] = r

    one_per_deployment = {}
    for r in requests:
        if not r.attributes.deployment:
            main_logger.log(
                f"Skipping removal request {r.id} since it was a cancellation."
            )
        elif r.attributes.deployment in one_per_deployment:
            main_logger.log(f"Skipping removal request {r.id} since it was superseded.")
        else:
            one_per_deployment[r.attributes.deployment] = r

    requests_to_check_for_payment = []
    for r in one_per_deployment.values():
        try:
            if r.attributes.deployment not in named_deployments:
                main_logger.log(
                    f"Skipping removal request {r.id} for {r.attributes.deployment} because it does"
                    f"not appear to refer to a live, named deployment."
                )
            elif skip_by_tag(r, include_tags, exclude_tags):
                main_logger.log(
                    "Skipping removal request %s, filtered by tag (include %s, exclude %s, present %s)"
                    % (r.id, include_tags, exclude_tags, r.attributes.tags)
                )
            elif r.id in removals_by_request:
                main_logger.log(
                    f"Found satisfied request for {r.id} at {removals_by_request[r.id].id}"
                )
            elif r.attributes.deployment in removals_by_deployment:
                main_logger.log(
                    f"Found removal record for indicated deployment {r.attributes.deployment} at "
                    f"{removals_by_deployment[r.attributes.deployment].id}"
                )
            else:
                if r.id not in previous_requests:
                    main_logger.log(f"Request {r.id} needs to processed.")
                    requests_to_check_for_payment.append(r)
                else:
                    main_logger.log(
                        f"Skipping unsatisfied request {r.id} because we have seen it before."
                    )
        except Exception as e:
            main_logger.log(f"ERROR examining {r.id}: {e}")

    requests_to_execute = []
    if min_required_payment:
        for r in requests_to_check_for_payment:
            main_logger.log(f"{r.id}: Confirming payment...")
            if confirm_payment(
                laconic, r, payment_address, min_required_payment, main_logger
            ):
                main_logger.log(f"{r.id}: Payment confirmed.")
                requests_to_execute.append(r)
            else:
                main_logger.log(f"Skipping request {r.id}: unable to verify payment.")
                dump_known_requests(state_file, [r])
    else:
        requests_to_execute = requests_to_check_for_payment

    main_logger.log(
        "Found %d unsatisfied request(s) to process." % len(requests_to_execute)
    )

    if not dry_run:
        for r in requests_to_execute:
            try:
                process_app_removal_request(
                    ctx,
                    laconic,
                    r,
                    os.path.abspath(deployment_parent_dir),
                    delete_volumes,
                    delete_names,
                )
            except Exception as e:
                main_logger.log(f"ERROR processing removal request {r.id}: {e}")
            finally:
                dump_known_requests(state_file, [r])
