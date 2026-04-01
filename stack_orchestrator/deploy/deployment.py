# Copyright © 2022, 2023 Vulcanize

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

import click
from pathlib import Path
import subprocess
import sys

from stack_orchestrator import constants
from stack_orchestrator.deploy.images import push_images_operation
from stack_orchestrator.deploy.deploy import (
    up_operation,
    down_operation,
    prepare_operation,
    ps_operation,
    port_operation,
    status_operation,
)
from stack_orchestrator.deploy.deploy import (
    exec_operation,
    logs_operation,
    create_deploy_context,
    update_envs_operation,
)
from stack_orchestrator.deploy.deploy_types import DeployCommandContext
from stack_orchestrator.deploy.deployment_context import DeploymentContext


@click.group()
@click.option("--dir", required=True, help="path to deployment directory")
@click.pass_context
def command(ctx, dir):
    """manage a deployment"""

    # Check that --stack wasn't supplied
    if ctx.parent.obj.stack:
        print("Error: --stack can't be supplied with the deployment command")
        sys.exit(1)
    # Check dir is valid
    dir_path = Path(dir)
    if not dir_path.exists():
        print(f"Error: deployment directory {dir} does not exist")
        sys.exit(1)
    if not dir_path.is_dir():
        print(
            f"Error: supplied deployment directory path {dir} exists but is a "
            "file not a directory"
        )
        sys.exit(1)
    # Store the deployment context for subcommands
    deployment_context = DeploymentContext()
    deployment_context.init(dir_path)
    ctx.obj = deployment_context


def make_deploy_context(ctx) -> DeployCommandContext:
    context: DeploymentContext = ctx.obj
    env_file = context.get_env_file()
    cluster_name = context.get_cluster_id()
    if constants.deploy_to_key in context.spec.obj:
        deployment_type = context.spec.obj[constants.deploy_to_key]
    else:
        deployment_type = constants.compose_deploy_type
    stack = context.deployment_dir
    return create_deploy_context(
        ctx.parent.parent.obj,
        context,
        stack,
        None,
        None,
        cluster_name,
        env_file,
        deployment_type,
    )


# TODO: remove legacy up command since it's an alias for start
@command.command()
@click.option(
    "--stay-attached/--detatch-terminal",
    default=False,
    help="detatch or not to see container stdout",
)
@click.option(
    "--skip-cluster-management/--perform-cluster-management",
    default=False,
    help="Skip cluster initialization/tear-down (only for kind-k8s deployments)",
)
@click.argument("extra_args", nargs=-1)  # help: command: up <service1> <service2>
@click.pass_context
def up(ctx, stay_attached, skip_cluster_management, extra_args):
    ctx.obj = make_deploy_context(ctx)
    services_list = list(extra_args) or None
    up_operation(ctx, services_list, stay_attached, skip_cluster_management)


# start is the preferred alias for up
@command.command()
@click.option(
    "--stay-attached/--detatch-terminal",
    default=False,
    help="detatch or not to see container stdout",
)
@click.option(
    "--skip-cluster-management/--perform-cluster-management",
    default=True,
    help="Skip cluster initialization/tear-down (only for kind-k8s deployments)",
)
@click.argument("extra_args", nargs=-1)  # help: command: up <service1> <service2>
@click.pass_context
def start(ctx, stay_attached, skip_cluster_management, extra_args):
    ctx.obj = make_deploy_context(ctx)
    services_list = list(extra_args) or None
    up_operation(ctx, services_list, stay_attached, skip_cluster_management)


@command.command()
@click.option(
    "--skip-cluster-management/--perform-cluster-management",
    default=False,
    help="Skip cluster initialization (only for kind-k8s deployments)",
)
@click.pass_context
def prepare(ctx, skip_cluster_management):
    """Create cluster infrastructure without starting pods.

    Sets up the kind cluster, namespace, PVs, PVCs, ConfigMaps, Services,
    and Ingresses — everything that 'start' does EXCEPT creating the
    Deployment resource. No pods will be scheduled.

    Use 'start --skip-cluster-management' afterward to create the Deployment
    and start pods when ready.
    """
    ctx.obj = make_deploy_context(ctx)
    prepare_operation(ctx, skip_cluster_management)


# TODO: remove legacy up command since it's an alias for stop
@command.command()
@click.option(
    "--delete-volumes/--preserve-volumes", default=False, help="delete data volumes"
)
@click.option(
    "--skip-cluster-management/--perform-cluster-management",
    default=True,
    help="Skip cluster initialization/tear-down (only for kind-k8s deployments)",
)
@click.argument("extra_args", nargs=-1)  # help: command: down <service1> <service2>
@click.pass_context
def down(ctx, delete_volumes, skip_cluster_management, extra_args):
    # Get the stack config file name
    # TODO: add cluster name and env file here
    ctx.obj = make_deploy_context(ctx)
    down_operation(ctx, delete_volumes, extra_args, skip_cluster_management)


# stop is the preferred alias for down
@command.command()
@click.option(
    "--delete-volumes/--preserve-volumes", default=False, help="delete data volumes"
)
@click.option(
    "--skip-cluster-management/--perform-cluster-management",
    default=True,
    help="Skip cluster initialization/tear-down (only for kind-k8s deployments)",
)
@click.argument("extra_args", nargs=-1)  # help: command: down <service1> <service2>
@click.pass_context
def stop(ctx, delete_volumes, skip_cluster_management, extra_args):
    # TODO: add cluster name and env file here
    ctx.obj = make_deploy_context(ctx)
    down_operation(ctx, delete_volumes, extra_args, skip_cluster_management)


@command.command()
@click.pass_context
def ps(ctx):
    ctx.obj = make_deploy_context(ctx)
    ps_operation(ctx)


@command.command()
@click.pass_context
def push_images(ctx):
    deploy_command_context: DeployCommandContext = make_deploy_context(ctx)
    deployment_context: DeploymentContext = ctx.obj
    push_images_operation(deploy_command_context, deployment_context)


@command.command()
@click.argument("extra_args", nargs=-1)  # help: command: port <service1> <service2>
@click.pass_context
def port(ctx, extra_args):
    ctx.obj = make_deploy_context(ctx)
    port_operation(ctx, extra_args)


@command.command()
@click.argument("extra_args", nargs=-1)  # help: command: exec <service> <command>
@click.pass_context
def exec(ctx, extra_args):
    ctx.obj = make_deploy_context(ctx)
    exec_operation(ctx, extra_args)


@command.command()
@click.option("--tail", "-n", default=None, help="number of lines to display")
@click.option("--follow", "-f", is_flag=True, default=False, help="follow log output")
@click.argument("extra_args", nargs=-1)  # help: command: logs <service1> <service2>
@click.pass_context
def logs(ctx, tail, follow, extra_args):
    ctx.obj = make_deploy_context(ctx)
    logs_operation(ctx, tail, follow, extra_args)


@command.command()
@click.pass_context
def status(ctx):
    ctx.obj = make_deploy_context(ctx)
    status_operation(ctx)


@command.command(name="update-envs")
@click.pass_context
def update_envs(ctx):
    ctx.obj = make_deploy_context(ctx)
    update_envs_operation(ctx)


@command.command()
@click.argument("job_name")
@click.option(
    "--helm-release",
    help="Helm release name (for k8s helm chart deployments, defaults to chart name)",
)
@click.pass_context
def run_job(ctx, job_name, helm_release):
    """run a one-time job from the stack"""
    from stack_orchestrator.deploy.deploy import run_job_operation

    ctx.obj = make_deploy_context(ctx)
    run_job_operation(ctx, job_name, helm_release)


@command.command()
@click.option("--stack-path", help="Path to stack git repo (overrides stored path)")
@click.option(
    "--spec-file", help="Path to GitOps spec.yml in repo (e.g., deployment/spec.yml)"
)
@click.option("--config-file", help="Config file to pass to deploy init")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Skip DNS verification",
)
@click.option(
    "--expected-ip",
    help="Expected IP for DNS verification (if different from egress)",
)
@click.option(
    "--image",
    multiple=True,
    help="Override container image: container=image",
)
@click.pass_context
def restart(ctx, stack_path, spec_file, config_file, force, expected_ip, image):
    """Pull latest code and restart deployment using git-tracked spec.

    GitOps workflow:
    1. Operator maintains spec.yml in their git repository
    2. This command pulls latest code (including updated spec.yml)
    3. If hostname changed, verifies DNS routes to this server
    4. Syncs deployment directory with the git-tracked spec
    5. Stops and restarts the deployment

    Data volumes are always preserved. The cluster is never destroyed.

    Stack source resolution (in order):
    1. --stack-path argument (if provided)
    2. stack-source field in deployment.yml (if stored)
    3. Error if neither available

    Note: spec.yml should be maintained in git, not regenerated from
    commands.py on each restart. Use 'deploy init' only for initial
    spec generation, then customize and commit to your operator repo.
    """
    from stack_orchestrator.util import get_yaml, get_parsed_deployment_spec
    from stack_orchestrator.deploy.deployment_create import create_operation
    from stack_orchestrator.deploy.dns_probe import verify_dns_via_probe

    deployment_context: DeploymentContext = ctx.obj

    # Parse --image flags into a dict of container_name -> image
    image_overrides = {}
    for entry in image:
        if "=" not in entry:
            raise click.BadParameter(
                f"Invalid --image format '{entry}', expected container=image",
                param_hint="'--image'",
            )
        container_name, image_ref = entry.split("=", 1)
        image_overrides[container_name] = image_ref

    # Get current spec info (before git pull)
    current_spec = deployment_context.spec
    current_http_proxy = current_spec.get_http_proxy()
    current_hostname = (
        current_http_proxy[0]["host-name"] if current_http_proxy else None
    )

    # Resolve stack source path
    if stack_path:
        stack_source = Path(stack_path).resolve()
    else:
        # Try to get from deployment.yml
        deployment_file = (
            deployment_context.deployment_dir / constants.deployment_file_name
        )
        deployment_data = get_yaml().load(open(deployment_file))
        stack_source_str = deployment_data.get("stack-source")
        if not stack_source_str:
            print(
                "Error: No stack-source in deployment.yml and --stack-path not provided"
            )
            print("Use --stack-path to specify the stack git repository location")
            sys.exit(1)
        stack_source = Path(stack_source_str)

    if not stack_source.exists():
        print(f"Error: Stack source path does not exist: {stack_source}")
        sys.exit(1)

    print("=== Deployment Restart ===")
    print(f"Deployment dir: {deployment_context.deployment_dir}")
    print(f"Stack source: {stack_source}")
    print(f"Current hostname: {current_hostname}")

    # Step 1: Git pull (brings in updated spec.yml from operator's repo)
    print("\n[1/4] Pulling latest code from stack repository...")
    git_result = subprocess.run(
        ["git", "pull"], cwd=stack_source, capture_output=True, text=True
    )
    if git_result.returncode != 0:
        print(f"Git pull failed: {git_result.stderr}")
        sys.exit(1)
    print(f"Git pull: {git_result.stdout.strip()}")

    # Determine spec file location
    # Priority: --spec-file argument > repo's deployment/spec.yml > deployment dir
    # Find repo root via git rather than assuming a fixed directory depth.
    git_root_result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=stack_source,
        capture_output=True,
        text=True,
    )
    if git_root_result.returncode == 0:
        repo_root = Path(git_root_result.stdout.strip())
    else:
        # Fallback: walk up from stack_source looking for .git
        repo_root = stack_source
        while repo_root != repo_root.parent:
            if (repo_root / ".git").exists():
                break
            repo_root = repo_root.parent
    if spec_file:
        # Spec file relative to repo root
        spec_file_path = repo_root / spec_file
    else:
        # Try standard GitOps location in repo
        gitops_spec = repo_root / "deployment" / "spec.yml"
        if gitops_spec.exists():
            spec_file_path = gitops_spec
        else:
            # Fall back to deployment directory
            spec_file_path = deployment_context.deployment_dir / "spec.yml"

    if not spec_file_path.exists():
        print(f"Error: spec.yml not found at {spec_file_path}")
        print("For GitOps, add spec.yml to your repo at deployment/spec.yml")
        print("Or specify --spec-file with path relative to repo root")
        sys.exit(1)

    print(f"Using spec: {spec_file_path}")

    # Parse spec to check for hostname changes
    new_spec_obj = get_parsed_deployment_spec(str(spec_file_path))
    new_http_proxy = new_spec_obj.get("network", {}).get("http-proxy", [])
    new_hostname = new_http_proxy[0]["host-name"] if new_http_proxy else None

    print(f"Spec hostname: {new_hostname}")

    # Step 2: DNS verification (only if hostname changed)
    if new_hostname and new_hostname != current_hostname:
        print(f"\n[2/4] Hostname changed: {current_hostname} -> {new_hostname}")
        if force:
            print("DNS verification skipped (--force)")
        else:
            print("Verifying DNS via probe...")
            if not verify_dns_via_probe(new_hostname):
                print(f"\nDNS verification failed for {new_hostname}")
                print("Ensure DNS is configured before restarting.")
                print("Use --force to skip this check.")
                sys.exit(1)
    else:
        print("\n[2/4] Hostname unchanged, skipping DNS verification")

    # Step 3: Sync deployment directory with spec
    # The spec's "stack:" value is often a relative path (e.g.
    # "stack-orchestrator/stacks/dumpster") that must resolve from the
    # repo root.  Change cwd so stack_is_external() sees it correctly.
    print("\n[3/4] Syncing deployment directory...")
    import os

    prev_cwd = os.getcwd()
    os.chdir(repo_root)
    deploy_ctx = make_deploy_context(ctx)
    create_operation(
        deployment_command_context=deploy_ctx,
        spec_file=str(spec_file_path),
        deployment_dir=str(deployment_context.deployment_dir),
        update=True,
        network_dir=None,
        initial_peers=None,
    )
    # Reload deployment context with updated spec
    deployment_context.init(deployment_context.deployment_dir)
    ctx.obj = deployment_context

    # Apply updated deployment.
    # If maintenance-service is configured, swap Ingress to maintenance
    # backend during the Recreate window so users see a branded page
    # instead of bare 502s.
    print("\n[4/4] Applying deployment update...")
    ctx.obj = make_deploy_context(ctx)

    # Check for maintenance service in the (reloaded) spec
    maintenance_svc = deployment_context.spec.get_maintenance_service()
    if maintenance_svc:
        print(f"Maintenance service configured: {maintenance_svc}")
        _restart_with_maintenance(
            ctx, deployment_context, maintenance_svc, image_overrides
        )
    else:
        up_operation(
            ctx,
            services_list=None,
            stay_attached=False,
            skip_cluster_management=True,
            image_overrides=image_overrides or None,
        )

    # Restore cwd after both create_operation and up_operation have run.
    # Both need the relative stack path to resolve from repo_root.
    os.chdir(prev_cwd)

    print("\n=== Restart Complete ===")
    print("Deployment updated via rolling update.")
    if new_hostname and new_hostname != current_hostname:
        print(f"\nNew hostname: {new_hostname}")
        print("Caddy will automatically provision TLS certificate.")


def _restart_with_maintenance(
    ctx, deployment_context, maintenance_svc, image_overrides
):
    """Restart with Ingress swap to maintenance service during Recreate.

    Flow:
    1. Deploy all pods (including maintenance pod) with up_operation
    2. Patch Ingress: swap all route backends to maintenance service
    3. Scale main (non-maintenance) Deployments to 0
    4. Scale main Deployments back up (triggers Recreate with new spec)
    5. Wait for readiness
    6. Patch Ingress: restore original backends

    This ensures the maintenance pod is already running before we touch
    the Ingress, and the main pods get a clean Recreate.
    """
    import time

    from kubernetes.client.exceptions import ApiException

    from stack_orchestrator.deploy.deploy import up_operation

    # Step 1: Apply the full deployment (creates/updates all pods + services)
    # This ensures maintenance pod exists before we swap Ingress to it.
    up_operation(
        ctx,
        services_list=None,
        stay_attached=False,
        skip_cluster_management=True,
        image_overrides=image_overrides or None,
    )

    # Parse maintenance service spec: "container-name:port"
    maint_container = maintenance_svc.split(":")[0]
    maint_port = int(maintenance_svc.split(":")[1])

    # Connect to k8s API
    deploy_ctx = ctx.obj
    deployer = deploy_ctx.deployer
    deployer.connect_api()
    namespace = deployer.k8s_namespace
    app_name = deployer.cluster_info.app_name
    networking_api = deployer.networking_api
    apps_api = deployer.apps_api

    ingress_name = f"{app_name}-ingress"

    # Step 2: Read current Ingress and save original backends
    try:
        ingress = networking_api.read_namespaced_ingress(
            name=ingress_name, namespace=namespace
        )
    except ApiException:
        print("Warning: No Ingress found, skipping maintenance swap")
        return

    # Resolve which service the maintenance container belongs to
    maint_service_name = deployer.cluster_info._resolve_service_name_for_container(
        maint_container
    )

    # Save original backends for restoration
    original_backends = []
    for rule in ingress.spec.rules:
        rule_backends = []
        for path in rule.http.paths:
            rule_backends.append(
                {
                    "name": path.backend.service.name,
                    "port": path.backend.service.port.number,
                }
            )
        original_backends.append(rule_backends)

    # Patch all Ingress backends to point to maintenance service
    print("Swapping Ingress to maintenance service...")
    for rule in ingress.spec.rules:
        for path in rule.http.paths:
            path.backend.service.name = maint_service_name
            path.backend.service.port.number = maint_port

    networking_api.replace_namespaced_ingress(
        name=ingress_name, namespace=namespace, body=ingress
    )
    print("Ingress now points to maintenance service")

    # Step 3: Find main (non-maintenance) Deployments and scale to 0
    # then back up to trigger a clean Recreate
    deployments_resp = apps_api.list_namespaced_deployment(
        namespace=namespace, label_selector=f"app={app_name}"
    )
    main_deployments = []
    for dep in deployments_resp.items:
        dep_name = dep.metadata.name
        # Skip maintenance deployments
        component = (dep.metadata.labels or {}).get("app.kubernetes.io/component", "")
        is_maintenance = maint_container in component
        if not is_maintenance:
            main_deployments.append(dep_name)

    if main_deployments:
        # Scale down main deployments
        for dep_name in main_deployments:
            print(f"Scaling down {dep_name}...")
            apps_api.patch_namespaced_deployment_scale(
                name=dep_name,
                namespace=namespace,
                body={"spec": {"replicas": 0}},
            )

        # Wait for pods to terminate
        print("Waiting for main pods to terminate...")
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            pods = deployer.core_api.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={app_name}",
            )
            # Count non-maintenance pods
            active = sum(
                1
                for p in pods.items
                if p.metadata
                and p.metadata.deletion_timestamp is None
                and not any(
                    maint_container in (c.name or "") for c in (p.spec.containers or [])
                )
            )
            if active == 0:
                break
            time.sleep(2)

        # Scale back up
        replicas = deployment_context.spec.get_replicas()
        for dep_name in main_deployments:
            print(f"Scaling up {dep_name} to {replicas} replicas...")
            apps_api.patch_namespaced_deployment_scale(
                name=dep_name,
                namespace=namespace,
                body={"spec": {"replicas": replicas}},
            )

        # Step 5: Wait for readiness
        print("Waiting for main pods to become ready...")
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            all_ready = True
            for dep_name in main_deployments:
                dep = apps_api.read_namespaced_deployment(
                    name=dep_name, namespace=namespace
                )
                ready = dep.status.ready_replicas or 0
                desired = dep.spec.replicas or 1
                if ready < desired:
                    all_ready = False
                    break
            if all_ready:
                break
            time.sleep(5)

    # Step 6: Restore original Ingress backends
    print("Restoring original Ingress backends...")
    ingress = networking_api.read_namespaced_ingress(
        name=ingress_name, namespace=namespace
    )
    for i, rule in enumerate(ingress.spec.rules):
        for j, path in enumerate(rule.http.paths):
            if i < len(original_backends) and j < len(original_backends[i]):
                path.backend.service.name = original_backends[i][j]["name"]
                path.backend.service.port.number = original_backends[i][j]["port"]

    networking_api.replace_namespaced_ingress(
        name=ingress_name, namespace=namespace, body=ingress
    )
    print("Ingress restored to original backends")
