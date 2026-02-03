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
import time
from stack_orchestrator import constants
from stack_orchestrator.deploy.images import push_images_operation
from stack_orchestrator.deploy.deploy import (
    up_operation,
    down_operation,
    ps_operation,
    port_operation,
    status_operation,
)
from stack_orchestrator.deploy.deploy import (
    exec_operation,
    logs_operation,
    create_deploy_context,
    update_operation,
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
    default=False,
    help="Skip cluster initialization/tear-down (only for kind-k8s deployments)",
)
@click.argument("extra_args", nargs=-1)  # help: command: up <service1> <service2>
@click.pass_context
def start(ctx, stay_attached, skip_cluster_management, extra_args):
    ctx.obj = make_deploy_context(ctx)
    services_list = list(extra_args) or None
    up_operation(ctx, services_list, stay_attached, skip_cluster_management)


# TODO: remove legacy up command since it's an alias for stop
@command.command()
@click.option(
    "--delete-volumes/--preserve-volumes", default=False, help="delete data volumes"
)
@click.option(
    "--skip-cluster-management/--perform-cluster-management",
    default=False,
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
    default=False,
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


@command.command()
@click.pass_context
def update(ctx):
    ctx.obj = make_deploy_context(ctx)
    update_operation(ctx)


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
@click.pass_context
def restart(ctx, stack_path, spec_file, config_file, force, expected_ip):
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
    if spec_file:
        # Spec file relative to repo root
        repo_root = stack_source.parent.parent.parent  # Go up from stack path
        spec_file_path = repo_root / spec_file
    else:
        # Try standard GitOps location in repo
        repo_root = stack_source.parent.parent.parent
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
    print("\n[3/4] Syncing deployment directory...")
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

    # Stop deployment
    print("\n[4/4] Restarting deployment...")
    ctx.obj = make_deploy_context(ctx)
    down_operation(
        ctx, delete_volumes=False, extra_args_list=[], skip_cluster_management=True
    )

    # Brief pause to ensure clean shutdown
    time.sleep(5)

    # Start deployment
    up_operation(
        ctx, services_list=None, stay_attached=False, skip_cluster_management=True
    )

    print("\n=== Restart Complete ===")
    print("Deployment restarted with git-tracked configuration.")
    if new_hostname and new_hostname != current_hostname:
        print(f"\nNew hostname: {new_hostname}")
        print("Caddy will automatically provision TLS certificate.")
