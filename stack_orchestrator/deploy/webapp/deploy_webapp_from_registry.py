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

from stack_orchestrator.deploy.images import remote_image_exists, add_tags_to_image
from stack_orchestrator.deploy.webapp import deploy_webapp
from stack_orchestrator.deploy.webapp.util import (LaconicRegistryClient, TimedLogger, TlsDetails,
                                                   build_container_image, push_container_image,
                                                   file_hash, deploy_to_k8s, publish_deployment,
                                                   hostname_for_deployment_request, generate_hostname_for_app,
                                                   match_owner, skip_by_tag)


def process_app_deployment_request(
    ctx,
    laconic: LaconicRegistryClient,
    app_deployment_request,
    deployment_record_namespace,
    dns_record_namespace,
    dns_suffix,
    deployment_parent_dir,
    kube_config,
    image_registry,
    force_rebuild,
    tls_details,
    logger,
):
    logger.log("BEGIN - process_app_deployment_request")

    # 1. look up application
    app = laconic.get_record(app_deployment_request.attributes.application, require=True)
    logger.log(f"Retrieved app record {app_deployment_request.attributes.application}")

    # 2. determine dns
    requested_name = hostname_for_deployment_request(app_deployment_request, laconic)
    logger.log(f"Determined requested name: {requested_name}")

    # HACK
    if "." in requested_name:
        raise Exception("Only unqualified hostnames allowed at this time.")

    fqdn = f"{requested_name}.{dns_suffix}"

    # 3. check ownership of existing dnsrecord vs this request
    # TODO: Support foreign DNS
    dns_crn = f"{dns_record_namespace}/{fqdn}"
    dns_record = laconic.get_record(dns_crn)
    if dns_record:
        matched_owner = match_owner(app_deployment_request, dns_record)
        if not matched_owner and dns_record.attributes.request:
            matched_owner = match_owner(app_deployment_request, laconic.get_record(dns_record.attributes.request, require=True))

        if matched_owner:
            logger.log(f"Matched DnsRecord ownership: {matched_owner}")
        else:
            raise Exception("Unable to confirm ownership of DnsRecord %s for request %s" %
                            (dns_record.id, app_deployment_request.id))

    # 4. get build and runtime config from request
    env_filename = None
    if app_deployment_request.attributes.config and "env" in app_deployment_request.attributes.config:
        env_filename = tempfile.mktemp()
        with open(env_filename, 'w') as file:
            for k, v in app_deployment_request.attributes.config["env"].items():
                file.write("%s=%s\n" % (k, shlex.quote(str(v))))

    # 5. determine new or existing deployment
    #   a. check for deployment crn
    app_deployment_crn = f"{deployment_record_namespace}/{fqdn}"
    if app_deployment_request.attributes.deployment:
        app_deployment_crn = app_deployment_request.attributes.deployment
    if not app_deployment_crn.startswith(deployment_record_namespace):
        raise Exception("Deployment CRN %s is not in a supported namespace" % app_deployment_request.attributes.deployment)

    deployment_record = laconic.get_record(app_deployment_crn)
    deployment_dir = os.path.join(deployment_parent_dir, fqdn)
    deployment_config_file = os.path.join(deployment_dir, "config.env")
    # TODO: Is there any reason not to simplify the hash input to the app_deployment_crn?
    deployment_container_tag = "laconic-webapp/%s:local" % hashlib.md5(deployment_dir.encode()).hexdigest()
    app_image_shared_tag = f"laconic-webapp/{app.id}:local"
    #   b. check for deployment directory (create if necessary)
    if not os.path.exists(deployment_dir):
        if deployment_record:
            raise Exception("Deployment record %s exists, but not deployment dir %s. Please remove name." %
                            (app_deployment_crn, deployment_dir))
        print("deploy_webapp", deployment_dir)
        deploy_webapp.create_deployment(ctx, deployment_dir, deployment_container_tag,
                                        f"https://{fqdn}", kube_config, image_registry, env_filename)
    elif env_filename:
        shutil.copyfile(env_filename, deployment_config_file)

    needs_k8s_deploy = False
    # 6. build container (if needed)
    if not deployment_record or deployment_record.attributes.application != app.id:
        needs_k8s_deploy = True
        # check if the image already exists
        shared_tag_exists = remote_image_exists(image_registry, app_image_shared_tag)
        if shared_tag_exists and not force_rebuild:
            # simply add our unique tag to the existing image and we are done
            logger.log(f"Using existing app image {app_image_shared_tag} for {deployment_container_tag}")
            add_tags_to_image(image_registry, app_image_shared_tag, deployment_container_tag)
            logger.log("Tag complete")
        else:
            extra_build_args = []  # TODO: pull from request
            logger.log(f"Building container image {deployment_container_tag}")
            build_container_image(app, deployment_container_tag, extra_build_args, logger)
            logger.log("Build complete")
            logger.log(f"Pushing container image {deployment_container_tag}")
            push_container_image(deployment_dir, logger)
            logger.log("Push complete")
            # The build/push commands above will use the unique deployment tag, so now we need to add the shared tag.
            logger.log(f"Updating app image tag {app_image_shared_tag} from build of {deployment_container_tag}")
            add_tags_to_image(image_registry, deployment_container_tag, app_image_shared_tag)
            logger.log("Tag complete")

    # 7. update config (if needed)
    if not deployment_record or file_hash(deployment_config_file) != deployment_record.attributes.meta.config:
        needs_k8s_deploy = True

    # 8. update k8s deployment
    if needs_k8s_deploy:
        deploy_to_k8s(
            deployment_record,
            deployment_dir,
            logger
        )

    logger.log("Publishing deployment to registry.")
    publish_deployment(
        laconic,
        app,
        deployment_record,
        app_deployment_crn,
        dns_record,
        dns_crn,
        deployment_dir,
        app_deployment_request,
        logger
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
        known_requests[r.id] = {
            "createTime": r.createTime,
            "status": status
        }
    with open(filename, "w") as f:
        json.dump(known_requests, f)


@click.command()
@click.option("--kube-config", help="Provide a config file for a k8s deployment")
@click.option("--laconic-config", help="Provide a config file for laconicd", required=True)
@click.option("--image-registry", help="Provide a container image registry url for this k8s cluster")
@click.option("--deployment-parent-dir", help="Create deployment directories beneath this directory", required=True)
@click.option("--request-id", help="The ApplicationDeploymentRequest to process")
@click.option("--discover", help="Discover and process all pending ApplicationDeploymentRequests", is_flag=True, default=False)
@click.option("--state-file", help="File to store state about previously seen requests.")
@click.option("--only-update-state", help="Only update the state file, don't process any requests anything.", is_flag=True)
@click.option("--dns-suffix", help="DNS domain to use eg, laconic.servesthe.world")
@click.option("--record-namespace-dns", help="eg, crn://laconic/dns")
@click.option("--record-namespace-deployments", help="eg, crn://laconic/deployments")
@click.option("--dry-run", help="Don't do anything, just report what would be done.", is_flag=True)
@click.option("--include-tags", help="Only include requests with matching tags (comma-separated).", default="")
@click.option("--exclude-tags", help="Exclude requests with matching tags (comma-separated).", default="")
@click.option("--force-rebuild", help="Rebuild even if the image already exists.", is_flag=True)
@click.option("--log-dir", help="Output build/deployment logs to directory.", default=None)
@click.option("--tls-host", help="Override TLS hostname (eg, '*.mydomain.com')")
@click.option("--tls-secret", help="Override TLS secret name")
@click.option("--tls-issuer", help="TLS issuer to use (default: letsencrypt-prod)")
@click.pass_context
def command(ctx, kube_config, laconic_config, image_registry, deployment_parent_dir,  # noqa: C901
            request_id, discover, state_file, only_update_state,
            dns_suffix, record_namespace_dns, record_namespace_deployments, dry_run,
            include_tags, exclude_tags, force_rebuild, log_dir, tls_host, tls_secret, tls_issuer):
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
        if not record_namespace_dns or not record_namespace_deployments or not dns_suffix:
            print("--dns-suffix, --record-namespace-dns, and --record-namespace-deployments are all required", file=sys.stderr)
            sys.exit(2)

    if (tls_secret and not tls_host) or (tls_host and not tls_secret):
        print("Cannot specify --tls-host without --tls-secret", file=sys.stderr)
        sys.exit(2)

    # Split CSV and clean up values.
    include_tags = [tag.strip() for tag in include_tags.split(",") if tag]
    exclude_tags = [tag.strip() for tag in exclude_tags.split(",") if tag]

    laconic = LaconicRegistryClient(laconic_config)

    # Find deployment requests.
    # single request
    if request_id:
        requests = [laconic.get_record(request_id, require=True)]
    # all requests
    elif discover:
        requests = laconic.app_deployment_requests()

    if only_update_state:
        if not dry_run:
            dump_known_requests(state_file, requests)
        return

    previous_requests = load_known_requests(state_file)

    # Collapse related requests.
    requests.sort(key=lambda r: r.createTime)
    requests.reverse()
    requests_by_name = {}
    skipped_by_name = {}
    for r in requests:
        # TODO: Do this _after_ filtering deployments and cancellations to minimize round trips.
        app = laconic.get_record(r.attributes.application)
        if not app:
            print("Skipping request %s, cannot locate app." % r.id)
            continue

        requested_name = r.attributes.dns
        if not requested_name:
            requested_name = generate_hostname_for_app(app)
            print("Generating name %s for request %s." % (requested_name, r.id))

        if requested_name in skipped_by_name or requested_name in requests_by_name:
            print("Ignoring request %s, it has been superseded." % r.id)
            continue

        if skip_by_tag(r, include_tags, exclude_tags):
            print("Skipping request %s, filtered by tag (include %s, exclude %s, present %s)" % (r.id,
                                                                                                 include_tags,
                                                                                                 exclude_tags,
                                                                                                 r.attributes.tags))
            skipped_by_name[requested_name] = r
            continue

        print("Found request %s to run application %s on %s." % (r.id, r.attributes.application, requested_name))
        requests_by_name[requested_name] = r

    # Find deployments.
    deployments = laconic.app_deployments()
    deployments_by_request = {}
    for d in deployments:
        if d.attributes.request:
            deployments_by_request[d.attributes.request] = d

    # Find removal requests.
    cancellation_requests = {}
    removal_requests = laconic.app_deployment_removal_requests()
    for r in removal_requests:
        if r.attributes.request:
            cancellation_requests[r.attributes.request] = r

    requests_to_execute = []
    for r in requests_by_name.values():
        if r.id in cancellation_requests and match_owner(cancellation_requests[r.id], r):
            print(f"Found deployment cancellation request for {r.id} at {cancellation_requests[r.id].id}")
        elif r.id in deployments_by_request:
            print(f"Found satisfied request for {r.id} at {deployments_by_request[r.id].id}")
        else:
            if r.id not in previous_requests:
                print(f"Request {r.id} needs to processed.")
                requests_to_execute.append(r)
            else:
                print(
                    f"Skipping unsatisfied request {r.id} because we have seen it before."
                )

    print("Found %d unsatisfied request(s) to process." % len(requests_to_execute))

    if not dry_run:
        tls_details = TlsDetails(tls_host, tls_secret, tls_issuer)
        for r in requests_to_execute:
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
                    print(f"Directing deployment logs to: {run_log_file_path}")
                    run_log_file = open(run_log_file_path, "wt")
                    run_reg_client = LaconicRegistryClient(laconic_config, log_file=run_log_file)

                logger = TimedLogger(run_id, run_log_file)
                logger.log("Processing ...")
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
                    tls_details,
                    logger
                )
                status = "DEPLOYED"
            except Exception as e:
                logger.log("ERROR: " + str(e))
            finally:
                if logger:
                    logger.log(f"DONE with status {status}", show_step_time=False, show_total_time=True)
                dump_known_requests(state_file, [r], status)
                if run_log_file:
                    run_log_file.close()
