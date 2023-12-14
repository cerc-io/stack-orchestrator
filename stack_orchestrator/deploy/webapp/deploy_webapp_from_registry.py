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
import shlex
import shutil
import sys
import tempfile

import click

from stack_orchestrator.deploy.webapp import deploy_webapp
from stack_orchestrator.deploy.webapp.util import (LaconicRegistryClient,
                                                   build_container_image, push_container_image,
                                                   file_hash, deploy_to_k8s, publish_deployment,
                                                   hostname_for_deployment_request, generate_hostname_for_app)


def process_app_deployment_request(
    ctx,
    laconic: LaconicRegistryClient,
    app_deployment_request,
    deployment_record_namespace,
    dns_record_namespace,
    dns_suffix,
    deployment_parent_dir,
    kube_config,
    image_registry
):
    # 1. look up application
    app = laconic.get_record(app_deployment_request.attributes.application, require=True)

    # 2. determine dns
    requested_name = hostname_for_deployment_request(app_deployment_request, laconic)

    # HACK
    if "." in requested_name:
        raise Exception("Only unqualified hostnames allowed at this time.")

    fqdn = f"{requested_name}.{dns_suffix}"
    container_tag = "%s:local" % app.attributes.name.replace("@", "")

    # 3. check ownership of existing dnsrecord vs this request
    # TODO: Support foreign DNS
    dns_crn = f"{dns_record_namespace}/{fqdn}"
    dns_record = laconic.get_record(dns_crn)
    if dns_record:
        dns_record_owners = dns_record.owners
        dns_request_owners = []
        if dns_record.request:
            prev_request = laconic.get_record(dns_record.request, require=True)
            dns_request_owners = prev_request.owners

        owner_match = None

        for owner in app_deployment_request.owners:
            if owner in dns_request_owners or owner in dns_record_owners:
                owner_match = owner
        if owner_match:
            print("Matched DnsRecord ownership to", owner)
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
    #   b. check for deployment directory (create if necessary)
    if not os.path.exists(deployment_dir):
        if deployment_record:
            raise ("Deployment record %s exists, but not deployment dir %s. Please remove name." %
                   (app_deployment_crn, deployment_dir))
        print("deploy_webapp", deployment_dir)
        deploy_webapp.create_deployment(ctx, deployment_dir, container_tag,
                                        f"https://{fqdn}", kube_config, image_registry, env_filename)
    elif env_filename:
        shutil.copyfile(env_filename, deployment_config_file)

    needs_k8s_deploy = False
    # 6. build container (if needed)
    if not deployment_record or deployment_record.attributes.application != app.id:
        build_container_image(app, container_tag)
        push_container_image(deployment_dir)
        needs_k8s_deploy = True

    # 7. update config (if needed)
    if not deployment_record or file_hash(deployment_config_file) != deployment_record.attributes.meta.config:
        needs_k8s_deploy = True

    # 8. update k8s deployment
    if needs_k8s_deploy:
        print("Deploying to k8s")
        deploy_to_k8s(
            deployment_record,
            deployment_dir,
        )

    publish_deployment(
        laconic,
        app,
        deployment_record,
        app_deployment_crn,
        dns_record,
        dns_crn,
        deployment_dir,
        app_deployment_request
    )


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
@click.option("--kube-config", help="Provide a config file for a k8s deployment")
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
@click.pass_context
def command(ctx, kube_config, laconic_config, image_registry, deployment_parent_dir,
            request_id, discover, state_file, only_update_state,
            dns_suffix, record_namespace_dns, record_namespace_deployments, dry_run):
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
    for r in requests:
        app = laconic.get_record(r.attributes.application)
        if not app:
            print("Skipping request %s, cannot locate app." % r.id)
            continue

        requested_name = r.attributes.dns
        if not requested_name:
            requested_name = generate_hostname_for_app(app)
            print("Generating name %s for request %s." % (requested_name, r.id))

        if requested_name not in requests_by_name:
            print(
                "Found request %s to run application %s on %s."
                % (r.id, r.attributes.application, requested_name)
            )
            requests_by_name[requested_name] = r
        else:
            print(
                "Ignoring request %s, it is superseded by %s."
                % (r.id, requests_by_name[requested_name].id)
            )

    # Find deployments.
    deployments = laconic.app_deployments()
    deployments_by_request = {}
    for d in deployments:
        if d.attributes.request:
            deployments_by_request[d.attributes.request] = d

    requests_to_execute = []
    for r in requests_by_name.values():
        if r.id not in deployments_by_request:
            if r.id not in previous_requests:
                print(f"Request {r.id} needs to processed.")
                requests_to_execute.append(r)
            else:
                print(
                    f"Skipping unsatisfied request {r.id} because we have seen it before."
                )
        else:
            print(f"Found satisfied request {r.id} at {deployments_by_request[r.id].names[0]}")

    print("Found %d unsatisfied request(s) to process." % len(requests_to_execute))

    if not dry_run:
        for r in requests_to_execute:
            try:
                process_app_deployment_request(
                    ctx,
                    laconic,
                    r,
                    record_namespace_deployments,
                    record_namespace_dns,
                    dns_suffix,
                    deployment_parent_dir,
                    kube_config,
                    image_registry
                )
            finally:
                dump_known_requests(state_file, [r])
