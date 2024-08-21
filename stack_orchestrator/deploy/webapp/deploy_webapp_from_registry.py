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

import hashlib
import json
import os
import shlex
import shutil
import sys
import tempfile
import time
import uuid

import click

from stack_orchestrator.deploy.images import remote_image_exists
from stack_orchestrator.deploy.webapp import deploy_webapp
from stack_orchestrator.deploy.webapp.util import (
    LaconicRegistryClient,
    TimedLogger,
    build_container_image,
    push_container_image,
    file_hash,
    deploy_to_k8s,
    publish_deployment,
    hostname_for_deployment_request,
    generate_hostname_for_app,
    match_owner,
    skip_by_tag,
    confirm_payment,
)


def process_app_deployment_request(
    ctx,
    laconic: LaconicRegistryClient,
    app_deployment_request,
    deployment_record_namespace,
    dns_record_namespace,
    default_dns_suffix,
    deployment_parent_dir,
    kube_config,
    image_registry,
    force_rebuild,
    fqdn_policy,
    recreate_on_deploy,
    payment_address,
    logger,
):
    logger.log("BEGIN - process_app_deployment_request")

    # 1. look up application
    app = laconic.get_record(
        app_deployment_request.attributes.application, require=True
    )
    logger.log(f"Retrieved app record {app_deployment_request.attributes.application}")

    # 2. determine dns
    requested_name = hostname_for_deployment_request(app_deployment_request, laconic)
    logger.log(f"Determined requested name: {requested_name}")

    if "." in requested_name:
        if "allow" == fqdn_policy or "preexisting" == fqdn_policy:
            fqdn = requested_name
        else:
            raise Exception(
                f"{requested_name} is invalid: only unqualified hostnames are allowed."
            )
    else:
        fqdn = f"{requested_name}.{default_dns_suffix}"

    # Normalize case (just in case)
    fqdn = fqdn.lower()

    # 3. check ownership of existing dnsrecord vs this request
    dns_lrn = f"{dns_record_namespace}/{fqdn}"
    dns_record = laconic.get_record(dns_lrn)
    if dns_record:
        matched_owner = match_owner(app_deployment_request, dns_record)
        if not matched_owner and dns_record.attributes.request:
            matched_owner = match_owner(
                app_deployment_request,
                laconic.get_record(dns_record.attributes.request, require=True),
            )

        if matched_owner:
            logger.log(f"Matched DnsRecord ownership: {matched_owner}")
        else:
            raise Exception(
                "Unable to confirm ownership of DnsRecord %s for request %s"
                % (dns_lrn, app_deployment_request.id)
            )
    elif "preexisting" == fqdn_policy:
        raise Exception(
            f"No pre-existing DnsRecord {dns_lrn} could be found for request {app_deployment_request.id}."
        )

    # 4. get build and runtime config from request
    env_filename = None
    if (
        app_deployment_request.attributes.config
        and "env" in app_deployment_request.attributes.config
    ):
        env_filename = tempfile.mktemp()
        with open(env_filename, "w") as file:
            for k, v in app_deployment_request.attributes.config["env"].items():
                file.write("%s=%s\n" % (k, shlex.quote(str(v))))

    # 5. determine new or existing deployment
    #   a. check for deployment lrn
    app_deployment_lrn = f"{deployment_record_namespace}/{fqdn}"
    if app_deployment_request.attributes.deployment:
        app_deployment_lrn = app_deployment_request.attributes.deployment
    if not app_deployment_lrn.startswith(deployment_record_namespace):
        raise Exception(
            "Deployment LRN %s is not in a supported namespace"
            % app_deployment_request.attributes.deployment
        )

    deployment_record = laconic.get_record(app_deployment_lrn)
    deployment_dir = os.path.join(deployment_parent_dir, fqdn)
    # At present we use this to generate a unique but stable ID for the app's host container
    # TODO: implement support to derive this transparently from the already-unique deployment id
    unique_deployment_id = hashlib.md5(fqdn.encode()).hexdigest()[:16]
    deployment_config_file = os.path.join(deployment_dir, "config.env")
    deployment_container_tag = "laconic-webapp/%s:local" % unique_deployment_id
    app_image_shared_tag = f"laconic-webapp/{app.id}:local"
    #   b. check for deployment directory (create if necessary)
    if not os.path.exists(deployment_dir):
        if deployment_record:
            raise Exception(
                "Deployment record %s exists, but not deployment dir %s. Please remove name."
                % (app_deployment_lrn, deployment_dir)
            )
        logger.log(
            f"Creating webapp deployment in: {deployment_dir} with container id: {deployment_container_tag}"
        )
        deploy_webapp.create_deployment(
            ctx,
            deployment_dir,
            deployment_container_tag,
            f"https://{fqdn}",
            kube_config,
            image_registry,
            env_filename,
        )
    elif env_filename:
        shutil.copyfile(env_filename, deployment_config_file)

    needs_k8s_deploy = False
    if force_rebuild:
        logger.log(
            "--force-rebuild is enabled so the container will always be built now, even if nothing has changed in the app"
        )
    # 6. build container (if needed)
    # TODO: add a comment that explains what this code is doing (not clear to me)
    if (
        not deployment_record
        or deployment_record.attributes.application != app.id
        or force_rebuild
    ):
        needs_k8s_deploy = True
        # check if the image already exists
        shared_tag_exists = remote_image_exists(image_registry, app_image_shared_tag)
        # Note: in the code below, calls to add_tags_to_image() won't work at present.
        # This is because SO deployment code in general re-names the container image
        # to be unique to the deployment. This is done transparently
        # and so when we call add_tags_to_image() here and try to add tags to the remote image,
        # we get the image name wrong. Accordingly I've disabled the relevant code for now.
        # This is safe because we are running with --force-rebuild at present
        if shared_tag_exists and not force_rebuild:
            # simply add our unique tag to the existing image and we are done
            logger.log(
                f"(SKIPPED) Existing image found for this app: {app_image_shared_tag} "
                "tagging it with: {deployment_container_tag} to use in this deployment"
            )
            # add_tags_to_image(image_registry, app_image_shared_tag, deployment_container_tag)
            logger.log("Tag complete")
        else:
            extra_build_args = []  # TODO: pull from request
            logger.log(f"Building container image: {deployment_container_tag}")
            build_container_image(
                app, deployment_container_tag, extra_build_args, logger
            )
            logger.log("Build complete")
            logger.log(f"Pushing container image: {deployment_container_tag}")
            push_container_image(deployment_dir, logger)
            logger.log("Push complete")
            # The build/push commands above will use the unique deployment tag, so now we need to add the shared tag.
            logger.log(
                f"(SKIPPED) Adding global app image tag: {app_image_shared_tag} to newly built image: {deployment_container_tag}"
            )
            # add_tags_to_image(image_registry, deployment_container_tag, app_image_shared_tag)
            logger.log("Tag complete")
    else:
        logger.log("Requested app is already deployed, skipping build and image push")

    # 7. update config (if needed)
    if (
        not deployment_record
        or file_hash(deployment_config_file) != deployment_record.attributes.meta.config
    ):
        needs_k8s_deploy = True

    # 8. update k8s deployment
    if needs_k8s_deploy:
        deploy_to_k8s(deployment_record, deployment_dir, recreate_on_deploy, logger)

    logger.log("Publishing deployment to registry.")
    publish_deployment(
        laconic,
        app,
        deployment_record,
        app_deployment_lrn,
        dns_record,
        dns_lrn,
        deployment_dir,
        app_deployment_request,
        payment_address,
        logger,
    )
    logger.log("Publication complete.")
    logger.log("END - process_app_deployment_request")


def load_known_requests(filename):
    if filename and os.path.exists(filename):
        return json.load(open(filename, "r"))
    return {}


def dump_known_requests(filename, requests, status="SEEN"):
    if not filename:
        return
    known_requests = load_known_requests(filename)
    for r in requests:
        known_requests[r.id] = {"createTime": r.createTime, "status": status}
    with open(filename, "w") as f:
        json.dump(known_requests, f)


@click.command()
@click.option("--kube-config", help="Provide a config file for a k8s deployment")
@click.option(
    "--laconic-config", help="Provide a config file for laconicd", required=True
)
@click.option(
    "--image-registry",
    help="Provide a container image registry url for this k8s cluster",
)
@click.option(
    "--deployment-parent-dir",
    help="Create deployment directories beneath this directory",
    required=True,
)
@click.option("--request-id", help="The ApplicationDeploymentRequest to process")
@click.option(
    "--discover",
    help="Discover and process all pending ApplicationDeploymentRequests",
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
@click.option("--dns-suffix", help="DNS domain to use eg, laconic.servesthe.world")
@click.option(
    "--fqdn-policy",
    help="How to handle requests with an FQDN: prohibit, allow, preexisting",
    default="prohibit",
)
@click.option("--record-namespace-dns", help="eg, lrn://laconic/dns")
@click.option("--record-namespace-deployments", help="eg, lrn://laconic/deployments")
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
    "--force-rebuild", help="Rebuild even if the image already exists.", is_flag=True
)
@click.option(
    "--recreate-on-deploy",
    help="Remove and recreate deployments instead of updating them.",
    is_flag=True,
)
@click.option(
    "--log-dir", help="Output build/deployment logs to directory.", default=None
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
    kube_config,
    laconic_config,
    image_registry,
    deployment_parent_dir,
    request_id,
    discover,
    state_file,
    only_update_state,
    dns_suffix,
    fqdn_policy,
    record_namespace_dns,
    record_namespace_deployments,
    dry_run,
    include_tags,
    exclude_tags,
    force_rebuild,
    recreate_on_deploy,
    log_dir,
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

    if not only_update_state:
        if (
            not record_namespace_dns
            or not record_namespace_deployments
            or not dns_suffix
        ):
            print(
                "--dns-suffix, --record-namespace-dns, and --record-namespace-deployments are all required",
                file=sys.stderr,
            )
            sys.exit(2)

    if fqdn_policy not in ["prohibit", "allow", "preexisting"]:
        print(
            "--fqdn-policy must be one of 'prohibit', 'allow', or 'preexisting'",
            file=sys.stderr,
        )
        sys.exit(2)

    main_logger = TimedLogger(file=sys.stderr)

    try:
        # Split CSV and clean up values.
        include_tags = [tag.strip() for tag in include_tags.split(",") if tag]
        exclude_tags = [tag.strip() for tag in exclude_tags.split(",") if tag]

        laconic = LaconicRegistryClient(laconic_config, log_file=sys.stderr)
        if not payment_address:
            payment_address = laconic.whoami().address

        main_logger.log(f"Payment address: {payment_address}")

        # Find deployment requests.
        # single request
        if request_id:
            main_logger.log(f"Retrieving request {request_id}...")
            requests = [laconic.get_record(request_id, require=True)]
        # all requests
        elif discover:
            main_logger.log("Discovering deployment requests...")
            if all_requests:
                requests = laconic.app_deployment_requests()
            else:
                requests = laconic.app_deployment_requests({"to": payment_address})

        if only_update_state:
            if not dry_run:
                dump_known_requests(state_file, requests)
            return

        previous_requests = {}
        if state_file:
            main_logger.log(f"Loading known requests from {state_file}...")
            previous_requests = load_known_requests(state_file)

        # Collapse related requests.
        requests.sort(key=lambda r: r.createTime)
        requests.reverse()
        requests_by_name = {}
        skipped_by_name = {}
        for r in requests:
            main_logger.log(f"BEGIN: Examining request {r.id}")
            result = "PENDING"
            try:
                if (
                    r.id in previous_requests
                    and previous_requests[r.id].get("status", "") != "RETRY"
                ):
                    main_logger.log(f"Skipping request {r.id}, we've already seen it.")
                    result = "SKIP"
                    continue

                app = laconic.get_record(r.attributes.application)
                if not app:
                    main_logger.log(f"Skipping request {r.id}, cannot locate app.")
                    result = "ERROR"
                    continue

                requested_name = r.attributes.dns
                if not requested_name:
                    requested_name = generate_hostname_for_app(app)
                    main_logger.log(
                        "Generating name %s for request %s." % (requested_name, r.id)
                    )

                if (
                    requested_name in skipped_by_name
                    or requested_name in requests_by_name
                ):
                    main_logger.log(
                        "Ignoring request %s, it has been superseded." % r.id
                    )
                    result = "SKIP"
                    continue

                if skip_by_tag(r, include_tags, exclude_tags):
                    main_logger.log(
                        "Skipping request %s, filtered by tag (include %s, exclude %s, present %s)"
                        % (r.id, include_tags, exclude_tags, r.attributes.tags)
                    )
                    skipped_by_name[requested_name] = r
                    result = "SKIP"
                    continue

                main_logger.log(
                    "Found pending request %s to run application %s on %s."
                    % (r.id, r.attributes.application, requested_name)
                )
                requests_by_name[requested_name] = r
            except Exception as e:
                result = "ERROR"
                main_logger.log(f"ERROR examining request {r.id}: " + str(e))
            finally:
                main_logger.log(f"DONE Examining request {r.id} with result {result}.")
                if result in ["ERROR"]:
                    dump_known_requests(state_file, [r], status=result)

        # Find deployments.
        main_logger.log("Discovering existing app deployments...")
        if all_requests:
            deployments = laconic.app_deployments()
        else:
            deployments = laconic.app_deployments({"by": payment_address})
        deployments_by_request = {}
        for d in deployments:
            if d.attributes.request:
                deployments_by_request[d.attributes.request] = d

        # Find removal requests.
        main_logger.log("Discovering deployment removal and cancellation requests...")
        cancellation_requests = {}
        removal_requests = laconic.app_deployment_removal_requests()
        for r in removal_requests:
            if r.attributes.request:
                cancellation_requests[r.attributes.request] = r

        requests_to_check_for_payment = []
        for r in requests_by_name.values():
            if r.id in cancellation_requests and match_owner(
                cancellation_requests[r.id], r
            ):
                main_logger.log(
                    f"Found deployment cancellation request for {r.id} at {cancellation_requests[r.id].id}"
                )
            elif r.id in deployments_by_request:
                main_logger.log(
                    f"Found satisfied request for {r.id} at {deployments_by_request[r.id].id}"
                )
            else:
                if (
                    r.id in previous_requests
                    and previous_requests[r.id].get("status", "") != "RETRY"
                ):
                    main_logger.log(
                        f"Skipping unsatisfied request {r.id} because we have seen it before."
                    )
                else:
                    main_logger.log(f"Request {r.id} needs to processed.")
                    requests_to_check_for_payment.append(r)

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
                    main_logger.log(
                        f"Skipping request {r.id}: unable to verify payment."
                    )
                    dump_known_requests(state_file, [r], status="UNPAID")
        else:
            requests_to_execute = requests_to_check_for_payment

        main_logger.log(
            "Found %d unsatisfied request(s) to process." % len(requests_to_execute)
        )

        if not dry_run:
            for r in requests_to_execute:
                main_logger.log(f"DEPLOYING {r.id}: BEGIN")
                dump_known_requests(state_file, [r], "DEPLOYING")
                status = "ERROR"
                run_log_file = None
                run_reg_client = laconic
                try:
                    run_id = f"{r.id}-{str(time.time()).split('.')[0]}-{str(uuid.uuid4()).split('-')[0]}"
                    if log_dir:
                        run_log_dir = os.path.join(log_dir, r.id)
                        if not os.path.exists(run_log_dir):
                            os.mkdir(run_log_dir)
                        run_log_file_path = os.path.join(run_log_dir, f"{run_id}.log")
                        main_logger.log(
                            f"Directing deployment logs to: {run_log_file_path}"
                        )
                        run_log_file = open(run_log_file_path, "wt")
                        run_reg_client = LaconicRegistryClient(
                            laconic_config, log_file=run_log_file
                        )

                    build_logger = TimedLogger(run_id, run_log_file)
                    build_logger.log("Processing ...")
                    process_app_deployment_request(
                        ctx,
                        run_reg_client,
                        r,
                        record_namespace_deployments,
                        record_namespace_dns,
                        dns_suffix,
                        os.path.abspath(deployment_parent_dir),
                        kube_config,
                        image_registry,
                        force_rebuild,
                        fqdn_policy,
                        recreate_on_deploy,
                        payment_address,
                        build_logger,
                    )
                    status = "DEPLOYED"
                except Exception as e:
                    main_logger.log(f"ERROR {r.id}:" + str(e))
                    build_logger.log("ERROR: " + str(e))
                finally:
                    main_logger.log(f"DEPLOYING {r.id}: END - {status}")
                    if build_logger:
                        build_logger.log(
                            f"DONE with status {status}",
                            show_step_time=False,
                            show_total_time=True,
                        )
                    dump_known_requests(state_file, [r], status)
                    if run_log_file:
                        run_log_file.close()
    except Exception as e:
        main_logger.log("UNCAUGHT ERROR:" + str(e))
        raise e
