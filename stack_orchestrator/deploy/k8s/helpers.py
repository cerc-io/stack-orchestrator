# Copyright © 2023 Vulcanize

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

from kubernetes import client, utils, watch
from kubernetes.client.exceptions import ApiException
import json
import os
from pathlib import Path
import subprocess
import re
import sys
from typing import Dict, Set, Mapping, List, Optional, cast
import yaml

from stack_orchestrator.util import get_k8s_dir, error_exit
from stack_orchestrator.opts import opts
from stack_orchestrator.deploy.deploy_util import parsed_pod_files_map_from_file_names
from stack_orchestrator.deploy.deployer import DeployerException
from stack_orchestrator import constants


def is_host_path_mount(volume_name: str) -> bool:
    """Check if a volume name is a host path mount (starts with /, ., or ~)."""
    return volume_name.startswith(("/", ".", "~"))


def sanitize_host_path_to_volume_name(host_path: str) -> str:
    """Convert a host path to a valid k8s volume name.

    K8s volume names must be lowercase, alphanumeric, with - allowed.
    E.g., '../config/test/script.sh' -> 'host-path-config-test-script-sh'
    """
    # Remove leading ./ or ../
    clean_path = re.sub(r"^\.+/", "", host_path)
    # Replace path separators and dots with hyphens
    name = re.sub(r"[/.]", "-", clean_path)
    # Remove any non-alphanumeric characters except hyphens
    name = re.sub(r"[^a-zA-Z0-9-]", "", name)
    # Convert to lowercase
    name = name.lower()
    # Remove leading/trailing hyphens and collapse multiple hyphens
    name = re.sub(r"-+", "-", name).strip("-")
    # Prefix with 'host-path-' to distinguish from named volumes
    return f"host-path-{name}"


def resolve_host_path_for_kind(host_path: str, deployment_dir: Path) -> Path:
    """Resolve a host path mount (relative to compose file) to absolute path.

    Compose files are in deployment_dir/compose/, so '../config/foo'
    resolves to deployment_dir/config/foo.
    """
    # The path is relative to the compose directory
    compose_dir = deployment_dir.joinpath("compose")
    resolved = compose_dir.joinpath(host_path).resolve()
    return resolved


def get_kind_host_path_mount_path(sanitized_name: str) -> str:
    """Get the path inside the kind node where a host path mount will be available."""
    return f"/mnt/{sanitized_name}"


def get_kind_cluster():
    """Get an existing kind cluster, if any.

    Uses `kind get clusters` to find existing clusters.
    Returns the cluster name or None if no cluster exists.
    """
    result = subprocess.run(
        "kind get clusters", shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        return None

    clusters = result.stdout.strip().splitlines()
    if clusters:
        return clusters[0]  # Return the first cluster found
    return None


def _run_command(command: str):
    if opts.o.debug:
        print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if opts.o.debug:
        print(f"Result: {result}")
    return result


def _caddy_cert_backup_file(kind_mount_root: str) -> Path:
    """Host path of the serialized caddy-system Secrets backup."""
    return Path(kind_mount_root) / "caddy-cert-backup" / "caddy-secrets.yaml"


def _read_caddy_cert_backup(kind_mount_root: str) -> Optional[str]:
    """Read the caddy cert backup file.

    The file is written by the in-cluster backup CronJob running as root
    (via kubectl image), so it lands on the host owned by root. Read it
    through an alpine container to sidestep permissions.
    """
    backup_file = _caddy_cert_backup_file(kind_mount_root)
    read_cmd = (
        f"docker run --rm -v {backup_file.parent}:/work:ro alpine:3.19 "
        f"sh -c 'test -f /work/{backup_file.name} && cat /work/{backup_file.name} "
        "|| true'"
    )
    result = subprocess.run(read_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: could not read {backup_file}: {result.stderr.strip()}")
        return None
    content = result.stdout
    return content if content.strip() else None


def _restore_caddy_certs(kind_mount_root: Optional[str]) -> None:
    """Restore manager=caddy Secrets from a prior cluster's backup.

    Runs BEFORE the Caddy ingress controller Deployment is applied. Caddy's
    secret_store driver reads existing certs at startup and skips ACME for
    any domain whose cert is already present — so restoring here avoids
    Let's Encrypt calls (and rate limits) on cluster recreate.
    """
    if not kind_mount_root:
        return
    content = _read_caddy_cert_backup(kind_mount_root)
    if not content:
        if opts.o.debug:
            print(
                f"No caddy cert backup at {_caddy_cert_backup_file(kind_mount_root)}, "
                "skipping restore"
            )
        return

    try:
        backup = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"Warning: invalid caddy cert backup yaml: {e}")
        return

    # `kubectl get -o yaml` wraps results in a List kind.
    items = backup.get("items", []) if isinstance(backup, dict) else []
    if not items:
        if opts.o.debug:
            print("Caddy cert backup has no items, skipping restore")
        return

    # Strip server-managed metadata so the objects apply cleanly on a
    # freshly-minted cluster.
    stale_fields = (
        "resourceVersion",
        "uid",
        "creationTimestamp",
        "selfLink",
        "generation",
        "managedFields",
    )
    for item in items:
        meta = item.get("metadata", {})
        for field in stale_fields:
            meta.pop(field, None)

    core_api = client.CoreV1Api()
    restored = 0
    for item in items:
        name = item.get("metadata", {}).get("name", "<unnamed>")
        try:
            core_api.create_namespaced_secret(namespace="caddy-system", body=item)
            restored += 1
            if opts.o.debug:
                print(f"  Restored secret: {name}")
        except ApiException as e:
            if e.status == 409:
                try:
                    core_api.replace_namespaced_secret(
                        name=name, namespace="caddy-system", body=item
                    )
                    restored += 1
                    if opts.o.debug:
                        print(f"  Updated secret: {name}")
                except ApiException as e2:
                    print(f"Warning: failed to replace caddy secret {name}: {e2}")
            else:
                print(f"Warning: failed to restore caddy secret {name}: {e}")
    print(f"Restored {restored}/{len(items)} caddy cert secret(s)")


def _install_caddy_cert_backup(
    api_client: client.ApiClient, kind_mount_root: Optional[str]
) -> None:
    """Deploy the CronJob that snapshots manager=caddy secrets to disk."""
    if not kind_mount_root:
        if opts.o.debug:
            print("No kind-mount-root configured; caddy cert backup disabled")
        return
    manifest = os.path.abspath(
        get_k8s_dir().joinpath(
            "components", "ingress", "caddy-cert-backup.yaml"
        )
    )
    with open(manifest) as f:
        objects = list(yaml.safe_load_all(f))
    utils.create_from_yaml(api_client, yaml_objects=objects)
    if opts.o.debug:
        print("Installed caddy cert backup CronJob")


def _parse_kind_extra_mounts(config_file: str) -> List[Dict[str, str]]:
    """Return the list of extraMounts declared in a kind config file."""
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        if opts.o.debug:
            print(f"Could not parse kind config {config_file}: {e}")
        return []
    mounts = []
    for node in config.get("nodes", []) or []:
        for m in node.get("extraMounts", []) or []:
            host_path = m.get("hostPath")
            container_path = m.get("containerPath")
            if host_path and container_path:
                mounts.append(
                    {"hostPath": host_path, "containerPath": container_path}
                )
    return mounts


def _get_control_plane_node(cluster_name: str) -> Optional[str]:
    """Return the kind control-plane node container name for a cluster."""
    result = subprocess.run(
        ["kind", "get", "nodes", "--name", cluster_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.endswith("control-plane"):
            return line
    return None


def _get_running_cluster_mounts(cluster_name: str) -> Dict[str, str]:
    """Return {containerPath: hostPath} for bind mounts on the control-plane."""
    node = _get_control_plane_node(cluster_name)
    if not node:
        return {}
    result = subprocess.run(
        ["docker", "inspect", node, "--format", "{{json .Mounts}}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    try:
        mounts = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return {}
    return {
        m["Destination"]: m["Source"]
        for m in mounts
        if m.get("Type") == "bind" and m.get("Destination") and m.get("Source")
    }


def check_mounts_compatible(cluster_name: str, config_file: str) -> None:
    """Fail if the new deployment's extraMounts aren't active on the cluster.

    Kind applies extraMounts only at cluster creation. When a deployment
    joins an existing cluster, any extraMount its kind-config declares that
    isn't already active on the running node will silently fall through to
    the node's overlay filesystem — data looks persisted but is lost on
    cluster destroy. Catch this up front.
    """
    required = _parse_kind_extra_mounts(config_file)
    if not required:
        return
    live = _get_running_cluster_mounts(cluster_name)
    if not live:
        # Could not inspect — don't block deployment, but warn.
        print(
            f"WARNING: could not inspect mounts on cluster '{cluster_name}'; "
            "skipping extraMount compatibility check",
            file=sys.stderr,
        )
        return
    mismatches = []
    for m in required:
        dest = m["containerPath"]
        want = m["hostPath"]
        have = live.get(dest)
        if have != want:
            mismatches.append((dest, want, have))
    if not mismatches:
        return
    lines = [
        f"This deployment declares extraMounts incompatible with the "
        f"running cluster '{cluster_name}':",
    ]
    for dest, want, have in mismatches:
        lines.append(
            f"  - {dest}: expected host path '{want}', "
            f"actual '{have or 'NOT MOUNTED'}'"
        )
    lines.append("")

    cluster_umbrella = live.get("/mnt")
    if cluster_umbrella:
        lines.extend(
            [
                f"The running cluster has an umbrella mount: "
                f"'{cluster_umbrella}' -> /mnt.",
                "",
                f"Fix: set 'kind-mount-root: {cluster_umbrella}' in this "
                "deployment's spec and place host paths for its volumes "
                f"under '{cluster_umbrella}/'. Kind applies extraMounts "
                "only at cluster creation, so new bind mounts cannot be "
                "added to the running cluster without a recreate — but "
                "the existing umbrella already covers any subdirectory "
                "you create on the host.",
            ]
        )
    else:
        lines.extend(
            [
                "The running cluster has no umbrella mount "
                "(no extraMount with containerPath=/mnt).",
                "",
                "Kind applies extraMounts only at cluster creation — "
                "neither kind nor Docker supports adding bind mounts to "
                "a running container. Without a recreate, any PV backed "
                "by one of the missing mounts will silently fall through "
                "to the node's overlay filesystem and lose data on "
                "cluster destroy.",
                "",
                "Fix: destroy and recreate the cluster with a kind-config "
                "that sets 'kind-mount-root' so future stacks can share "
                "an umbrella without recreating.",
            ]
        )
    lines.append("")
    lines.append("See docs/deployment_patterns.md.")
    raise DeployerException("\n".join(lines))


def _warn_if_no_umbrella(config_file: str) -> None:
    """Warn if creating a cluster without a '/mnt' umbrella mount.

    Without an umbrella, future stacks joining this cluster that need new
    host-path mounts will fail the compatibility check and require a full
    cluster recreate to add them.
    """
    mounts = _parse_kind_extra_mounts(config_file)
    if any(m.get("containerPath") == "/mnt" for m in mounts):
        return
    print(
        "WARNING: creating kind cluster without an umbrella mount "
        "('kind-mount-root' not set). Future stacks added to this cluster "
        "that require new host-path mounts will not be able to without a "
        "full cluster recreate. See docs/deployment_patterns.md.",
        file=sys.stderr,
    )


def create_cluster(name: str, config_file: str):
    """Create or reuse the single kind cluster for this host.

    There is only one kind cluster per host by design. Multiple deployments
    share this cluster. If a cluster already exists, it is reused.

    Args:
        name: Cluster name (used only when creating the first cluster)
        config_file: Path to kind config file (used only when creating)

    Returns:
        The name of the cluster being used
    """
    existing = get_kind_cluster()
    if existing:
        print(f"Using existing cluster: {existing}")
        check_mounts_compatible(existing, config_file)
        return existing

    _warn_if_no_umbrella(config_file)
    print(f"Creating new cluster: {name}")
    result = _run_command(f"kind create cluster --name {name} --config {config_file}")
    if result.returncode != 0:
        raise DeployerException(f"kind create cluster failed: {result}")
    return name


def destroy_cluster(name: str):
    _run_command(f"kind delete cluster --name {name}")


def is_ingress_running() -> bool:
    """Check if the Caddy ingress controller is already running in the cluster."""
    try:
        core_v1 = client.CoreV1Api()
        pods = core_v1.list_namespaced_pod(
            namespace="caddy-system",
            label_selector=(
                "app.kubernetes.io/name=caddy-ingress-controller,"
                "app.kubernetes.io/component=controller"
            ),
        )
        for pod in pods.items:
            if pod.status and pod.status.container_statuses:
                if pod.status.container_statuses[0].ready is True:
                    if opts.o.debug:
                        print("Caddy ingress controller already running")
                    return True
        return False
    except ApiException:
        return False


def wait_for_ingress_in_kind():
    core_v1 = client.CoreV1Api()
    for i in range(20):
        warned_waiting = False
        w = watch.Watch()
        for event in w.stream(
            func=core_v1.list_namespaced_pod,
            namespace="caddy-system",
            label_selector=(
                "app.kubernetes.io/name=caddy-ingress-controller,"
                "app.kubernetes.io/component=controller"
            ),
            timeout_seconds=30,
        ):
            event_dict = cast(dict, event)
            pod = cast(client.V1Pod, event_dict.get("object"))
            if pod and pod.status and pod.status.container_statuses:
                if pod.status.container_statuses[0].ready is True:
                    if warned_waiting:
                        print("Caddy ingress controller is ready")
                    return
            print("Waiting for Caddy ingress controller to become ready...")
            warned_waiting = True
    error_exit("ERROR: Timed out waiting for Caddy ingress to become ready")


def install_ingress_for_kind(
    acme_email: str = "", kind_mount_root: Optional[str] = None
):
    api_client = client.ApiClient()
    ingress_install = os.path.abspath(
        get_k8s_dir().joinpath(
            "components", "ingress", "ingress-caddy-kind-deploy.yaml"
        )
    )
    if opts.o.debug:
        print("Installing Caddy ingress controller in kind cluster")

    # Template the YAML with email before applying
    with open(ingress_install) as f:
        yaml_content = f.read()

    if acme_email:
        yaml_content = yaml_content.replace('email: ""', f'email: "{acme_email}"')
        if opts.o.debug:
            print(f"Configured Caddy with ACME email: {acme_email}")

    yaml_objects = list(yaml.safe_load_all(yaml_content))

    # Split: apply everything except the Caddy controller Deployment first,
    # so the namespace + secrets exist before the pod can start and read its
    # secret_store. Race-free: Caddy has no way to see the cluster until
    # its Deployment object is created in Phase 3.
    def _is_caddy_deployment(o):
        return (
            o.get("kind") == "Deployment"
            and o.get("metadata", {}).get("name") == "caddy-ingress-controller"
        )

    pre_deployment = [o for o in yaml_objects if not _is_caddy_deployment(o)]
    caddy_deployment = [o for o in yaml_objects if _is_caddy_deployment(o)]

    # Phase 1: namespace, SA, RBAC, ConfigMap, Service, IngressClass
    utils.create_from_yaml(api_client, yaml_objects=pre_deployment)

    # Patch ConfigMap with ACME email if provided
    if acme_email:
        if opts.o.debug:
            print(f"Configuring ACME email: {acme_email}")
        core_api = client.CoreV1Api()
        configmap = core_api.read_namespaced_config_map(
            name="caddy-ingress-controller-configmap", namespace="caddy-system"
        )
        configmap.data["email"] = acme_email
        core_api.patch_namespaced_config_map(
            name="caddy-ingress-controller-configmap",
            namespace="caddy-system",
            body=configmap,
        )

    # Phase 2: restore caddy cert secrets before Caddy can start
    _restore_caddy_certs(kind_mount_root)

    # Phase 3: start Caddy (reads restored secrets on startup)
    utils.create_from_yaml(api_client, yaml_objects=caddy_deployment)

    # Install the backup CronJob last — it targets the same namespace and
    # depends on nothing in the Caddy Deployment.
    _install_caddy_cert_backup(api_client, kind_mount_root)


def load_images_into_kind(kind_cluster_name: str, image_set: Set[str]):
    for image in image_set:
        result = _run_command(
            f"kind load docker-image {image} --name {kind_cluster_name}"
        )
        if result.returncode != 0:
            raise DeployerException(f"kind load docker-image failed: {result}")


def pods_in_deployment(
    core_api: client.CoreV1Api, deployment_name: str, namespace: str = "default"
):
    pods = []
    pod_response = core_api.list_namespaced_pod(
        namespace=namespace, label_selector=f"app={deployment_name}"
    )
    if opts.o.debug:
        print(f"pod_response: {pod_response}")
    for pod_info in pod_response.items:
        pod_name = pod_info.metadata.name
        pods.append(pod_name)
    return pods


def containers_in_pod(
    core_api: client.CoreV1Api, pod_name: str, namespace: str = "default"
) -> List[str]:
    containers: List[str] = []
    pod_response = cast(
        client.V1Pod, core_api.read_namespaced_pod(pod_name, namespace=namespace)
    )
    if opts.o.debug:
        print(f"pod_response: {pod_response}")
    if not pod_response.spec or not pod_response.spec.containers:
        return containers
    for pod_container in pod_response.spec.containers:
        if pod_container.name:
            containers.append(pod_container.name)
    return containers


def log_stream_from_string(s: str):
    # Note response has to be UTF-8 encoded because the caller expects to decode it
    yield ("ignore", s.encode())


def named_volumes_from_pod_files(parsed_pod_files):
    # Parse the compose files looking for named volumes
    named_volumes = []
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "volumes" in parsed_pod_file:
            volumes = parsed_pod_file["volumes"]
            for volume, value in volumes.items():
                # Volume definition looks like:
                # 'laconicd-data': None
                named_volumes.append(volume)
    return named_volumes


def get_kind_pv_bind_mount_path(
    volume_name: str,
    kind_mount_root: Optional[str] = None,
    host_path: Optional[str] = None,
):
    """Get the path inside the Kind node for a PV.

    When kind-mount-root is set and the volume's host path is under
    that root, return /mnt/{relative_path} so it resolves through the
    single root extraMount. Otherwise fall back to /mnt/{volume_name}.
    """
    if kind_mount_root and host_path and host_path.startswith(kind_mount_root):
        rel = os.path.relpath(host_path, kind_mount_root)
        return f"/mnt/{rel}"
    return f"/mnt/{volume_name}"


def volume_mounts_for_service(parsed_pod_files, service):
    result = []
    # Find the service
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "services" in parsed_pod_file:
            services = parsed_pod_file["services"]
            for service_name in services:
                if service_name == service:
                    service_obj = services[service_name]
                    if "volumes" in service_obj:
                        volumes = service_obj["volumes"]
                        for mount_string in volumes:
                            # Looks like: test-data:/data
                            # or test-data:/data:ro or test-data:/data:rw
                            # or ../config/file.sh:/opt/file.sh (host path mount)
                            if opts.o.debug:
                                print(f"mount_string: {mount_string}")
                            mount_split = mount_string.split(":")
                            volume_name = mount_split[0]
                            mount_path = mount_split[1]
                            mount_options = (
                                mount_split[2] if len(mount_split) == 3 else None
                            )
                            # For host path mounts, use sanitized name
                            if is_host_path_mount(volume_name):
                                k8s_volume_name = sanitize_host_path_to_volume_name(
                                    volume_name
                                )
                            else:
                                k8s_volume_name = volume_name
                            if opts.o.debug:
                                print(f"volume_name: {volume_name}")
                                print(f"k8s_volume_name: {k8s_volume_name}")
                                print(f"mount path: {mount_path}")
                                print(f"mount options: {mount_options}")
                            volume_device = client.V1VolumeMount(
                                mount_path=mount_path,
                                name=k8s_volume_name,
                                read_only="ro" == mount_options,
                            )
                            result.append(volume_device)
    return result


def volumes_for_pod_files(parsed_pod_files, spec, app_name):
    result = []
    seen_host_path_volumes = set()  # Track host path volumes to avoid duplicates

    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]

        # Handle named volumes from top-level volumes section
        if "volumes" in parsed_pod_file:
            volumes = parsed_pod_file["volumes"]
            for volume_name in volumes.keys():
                if volume_name in spec.get_configmaps():
                    # Set defaultMode=0o755 to make scripts executable
                    config_map = client.V1ConfigMapVolumeSource(
                        name=f"{app_name}-{volume_name}", default_mode=0o755
                    )
                    volume = client.V1Volume(name=volume_name, config_map=config_map)
                    result.append(volume)
                else:
                    claim = client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=f"{app_name}-{volume_name}"
                    )
                    volume = client.V1Volume(
                        name=volume_name, persistent_volume_claim=claim
                    )
                    result.append(volume)

        # Handle host path mounts from service volumes
        if "services" in parsed_pod_file:
            services = parsed_pod_file["services"]
            for service_name in services:
                service_obj = services[service_name]
                if "volumes" in service_obj:
                    for mount_string in service_obj["volumes"]:
                        mount_split = mount_string.split(":")
                        volume_source = mount_split[0]
                        if is_host_path_mount(volume_source):
                            sanitized_name = sanitize_host_path_to_volume_name(
                                volume_source
                            )
                            if sanitized_name not in seen_host_path_volumes:
                                seen_host_path_volumes.add(sanitized_name)
                                # Create hostPath volume for mount inside kind node
                                kind_mount_path = get_kind_host_path_mount_path(
                                    sanitized_name
                                )
                                host_path_source = client.V1HostPathVolumeSource(
                                    path=kind_mount_path, type="FileOrCreate"
                                )
                                volume = client.V1Volume(
                                    name=sanitized_name, host_path=host_path_source
                                )
                                result.append(volume)
                                if opts.o.debug:
                                    print(f"Created hostPath volume: {sanitized_name}")
    return result


def _get_host_paths_for_volumes(deployment_context):
    return deployment_context.spec.get_volumes()


def _make_absolute_host_path(data_mount_path: Path, deployment_dir: Path) -> Path:
    if os.path.isabs(data_mount_path):
        return data_mount_path
    else:
        # Python Path voodo that looks pretty odd:
        return Path.cwd().joinpath(deployment_dir.joinpath(data_mount_path)).resolve()


def _generate_kind_mounts(parsed_pod_files, deployment_dir, deployment_context):
    volume_definitions = []
    volume_host_path_map = _get_host_paths_for_volumes(deployment_context)
    seen_host_path_mounts = set()  # Track to avoid duplicate mounts
    kind_mount_root = deployment_context.spec.get_kind_mount_root()

    # When kind-mount-root is set, emit a single extraMount for the root.
    # Individual volumes whose host path starts with the root are covered
    # by this single mount and don't need their own extraMount entries.
    mount_root_emitted = False
    if kind_mount_root:
        volume_definitions.append(
            f"  - hostPath: {kind_mount_root}\n"
            f"    containerPath: /mnt\n"
            f"    propagation: HostToContainer\n"
        )
        mount_root_emitted = True

    # Note these paths are relative to the location of the pod files (at present)
    # So we need to fix up to make them correct and absolute because kind assumes
    # relative to the cwd.
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "services" in parsed_pod_file:
            services = parsed_pod_file["services"]
            for service_name in services:
                service_obj = services[service_name]
                if "volumes" in service_obj:
                    volumes = service_obj["volumes"]
                    for mount_string in volumes:
                        # Looks like: test-data:/data
                        # or test-data:/data:ro or test-data:/data:rw
                        # or ../config/file.sh:/opt/file.sh (host path mount)
                        if opts.o.debug:
                            print(f"mount_string: {mount_string}")
                        mount_split = mount_string.split(":")
                        volume_name = mount_split[0]
                        mount_path = mount_split[1]

                        if is_host_path_mount(volume_name):
                            # Host path mount - add extraMount for kind
                            sanitized_name = sanitize_host_path_to_volume_name(
                                volume_name
                            )
                            if sanitized_name not in seen_host_path_mounts:
                                seen_host_path_mounts.add(sanitized_name)
                                # Resolve path relative to compose directory
                                host_path = resolve_host_path_for_kind(
                                    volume_name, deployment_dir
                                )
                                container_path = get_kind_host_path_mount_path(
                                    sanitized_name
                                )
                                volume_definitions.append(
                                    f"  - hostPath: {host_path}\n"
                                    f"    containerPath: {container_path}\n"
                                    f"    propagation: HostToContainer\n"
                                )
                                if opts.o.debug:
                                    print(f"Added host path mount: {host_path}")
                        else:
                            # Named volume
                            if opts.o.debug:
                                print(f"volume_name: {volume_name}")
                                print(f"map: {volume_host_path_map}")
                                print(f"mount path: {mount_path}")
                            if (
                                volume_name
                                not in deployment_context.spec.get_configmaps()
                            ):
                                if (
                                    volume_name in volume_host_path_map
                                    and volume_host_path_map[volume_name]
                                ):
                                    host_path = _make_absolute_host_path(
                                        volume_host_path_map[volume_name],
                                        deployment_dir,
                                    )
                                    # Skip individual extraMount if covered
                                    # by the kind-mount-root single mount
                                    if mount_root_emitted and str(host_path).startswith(
                                        kind_mount_root
                                    ):
                                        continue
                                    container_path = get_kind_pv_bind_mount_path(
                                        volume_name
                                    )
                                    volume_definitions.append(
                                        f"  - hostPath: {host_path}\n"
                                        f"    containerPath: {container_path}\n"
                                        f"    propagation: HostToContainer\n"
                                    )
    return (
        ""
        if len(volume_definitions) == 0
        else ("  extraMounts:\n" f"{''.join(volume_definitions)}")
    )


# TODO: decide if we need this functionality
def _generate_kind_port_mappings_from_services(parsed_pod_files):
    port_definitions = []
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "services" in parsed_pod_file:
            services = parsed_pod_file["services"]
            for service_name in services:
                service_obj = services[service_name]
                if "ports" in service_obj:
                    ports = service_obj["ports"]
                    for port_string in ports:
                        # TODO handle the complex cases
                        # Looks like: 80 or something more complicated
                        port_definitions.append(
                            f"  - containerPort: {port_string}\n"
                            f"    hostPort: {port_string}\n"
                        )
    return (
        ""
        if len(port_definitions) == 0
        else ("  extraPortMappings:\n" f"{''.join(port_definitions)}")
    )


def _generate_kind_port_mappings(parsed_pod_files):
    port_definitions = []
    seen = set()
    # Map port 80 and 443 for the Caddy ingress controller (HTTPS support)
    for port_string in ["80", "443"]:
        port_definitions.append(
            f"  - containerPort: {port_string}\n    hostPort: {port_string}\n"
        )
        seen.add((port_string, "TCP"))
    # Map ports only for services with network_mode: host.
    # Other service ports are internal — they go through the Ingress on
    # 80/443 and don't need host port mappings. Mapping all compose ports
    # unconditionally (the previous behavior) caused conflicts with local
    # services like postgres (5432) and redis (6379).
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
        if "services" in parsed_pod_file:
            for service_name in parsed_pod_file["services"]:
                service_obj = parsed_pod_file["services"][service_name]
                if service_obj.get("network_mode") != "host":
                    continue
                for port_entry in service_obj.get("ports", []):
                    port_str = str(port_entry)
                    protocol = "TCP"
                    if "/" in port_str:
                        port_str, proto = port_str.split("/", 1)
                        protocol = proto.upper()
                    if ":" in port_str:
                        port_str = port_str.split(":")[-1]
                    port_num = port_str.strip("'\"")
                    if (port_num, protocol) not in seen:
                        seen.add((port_num, protocol))
                        port_definitions.append(
                            f"  - containerPort: {port_num}\n"
                            f"    hostPort: {port_num}\n"
                            f"    protocol: {protocol}\n"
                        )
    return (
        ""
        if len(port_definitions) == 0
        else ("  extraPortMappings:\n" f"{''.join(port_definitions)}")
    )


def _generate_high_memlock_spec_mount(deployment_dir: Path):
    """Generate the extraMount entry for high-memlock-spec.json.

    The spec file must be mounted at the same path inside the kind node
    as it appears on the host, because containerd's base_runtime_spec
    references an absolute path.
    """
    spec_path = deployment_dir.joinpath(constants.high_memlock_spec_filename).resolve()
    return (
        f"  - hostPath: {spec_path}\n"
        f"    containerPath: {spec_path}\n"
        f"    propagation: HostToContainer\n"
    )


def generate_high_memlock_spec_json():
    """Generate OCI spec JSON with unlimited RLIMIT_MEMLOCK.

    This is needed for workloads like Solana validators that require large
    amounts of locked memory for memory-mapped files during snapshot decompression.

    The IPC_LOCK capability alone doesn't raise the RLIMIT_MEMLOCK limit - it only
    allows mlock() calls. We need to set the rlimit in the OCI runtime spec.

    IMPORTANT: This must be a complete OCI runtime spec, not just the rlimits
    section. The spec is based on kind's default cri-base.json with rlimits added.
    """
    import json

    # Use maximum 64-bit signed integer value for unlimited
    max_rlimit = 9223372036854775807
    # Based on kind's /etc/containerd/cri-base.json with rlimits added
    spec = {
        "ociVersion": "1.1.0-rc.1",
        "process": {
            "user": {"uid": 0, "gid": 0},
            "cwd": "/",
            "capabilities": {
                "bounding": [
                    "CAP_CHOWN",
                    "CAP_DAC_OVERRIDE",
                    "CAP_FSETID",
                    "CAP_FOWNER",
                    "CAP_MKNOD",
                    "CAP_NET_RAW",
                    "CAP_SETGID",
                    "CAP_SETUID",
                    "CAP_SETFCAP",
                    "CAP_SETPCAP",
                    "CAP_NET_BIND_SERVICE",
                    "CAP_SYS_CHROOT",
                    "CAP_KILL",
                    "CAP_AUDIT_WRITE",
                ],
                "effective": [
                    "CAP_CHOWN",
                    "CAP_DAC_OVERRIDE",
                    "CAP_FSETID",
                    "CAP_FOWNER",
                    "CAP_MKNOD",
                    "CAP_NET_RAW",
                    "CAP_SETGID",
                    "CAP_SETUID",
                    "CAP_SETFCAP",
                    "CAP_SETPCAP",
                    "CAP_NET_BIND_SERVICE",
                    "CAP_SYS_CHROOT",
                    "CAP_KILL",
                    "CAP_AUDIT_WRITE",
                ],
                "permitted": [
                    "CAP_CHOWN",
                    "CAP_DAC_OVERRIDE",
                    "CAP_FSETID",
                    "CAP_FOWNER",
                    "CAP_MKNOD",
                    "CAP_NET_RAW",
                    "CAP_SETGID",
                    "CAP_SETUID",
                    "CAP_SETFCAP",
                    "CAP_SETPCAP",
                    "CAP_NET_BIND_SERVICE",
                    "CAP_SYS_CHROOT",
                    "CAP_KILL",
                    "CAP_AUDIT_WRITE",
                ],
            },
            "rlimits": [
                {"type": "RLIMIT_MEMLOCK", "hard": max_rlimit, "soft": max_rlimit},
                {"type": "RLIMIT_NOFILE", "hard": 1048576, "soft": 1048576},
            ],
            "noNewPrivileges": True,
        },
        "root": {"path": "rootfs"},
        "mounts": [
            {
                "destination": "/proc",
                "type": "proc",
                "source": "proc",
                "options": ["nosuid", "noexec", "nodev"],
            },
            {
                "destination": "/dev",
                "type": "tmpfs",
                "source": "tmpfs",
                "options": ["nosuid", "strictatime", "mode=755", "size=65536k"],
            },
            {
                "destination": "/dev/pts",
                "type": "devpts",
                "source": "devpts",
                "options": [
                    "nosuid",
                    "noexec",
                    "newinstance",
                    "ptmxmode=0666",
                    "mode=0620",
                    "gid=5",
                ],
            },
            {
                "destination": "/dev/shm",
                "type": "tmpfs",
                "source": "shm",
                "options": ["nosuid", "noexec", "nodev", "mode=1777", "size=65536k"],
            },
            {
                "destination": "/dev/mqueue",
                "type": "mqueue",
                "source": "mqueue",
                "options": ["nosuid", "noexec", "nodev"],
            },
            {
                "destination": "/sys",
                "type": "sysfs",
                "source": "sysfs",
                "options": ["nosuid", "noexec", "nodev", "ro"],
            },
            {
                "destination": "/run",
                "type": "tmpfs",
                "source": "tmpfs",
                "options": ["nosuid", "strictatime", "mode=755", "size=65536k"],
            },
        ],
        "linux": {
            "resources": {"devices": [{"allow": False, "access": "rwm"}]},
            "cgroupsPath": "/default",
            "namespaces": [
                {"type": "pid"},
                {"type": "ipc"},
                {"type": "uts"},
                {"type": "mount"},
                {"type": "network"},
            ],
            "maskedPaths": [
                "/proc/acpi",
                "/proc/asound",
                "/proc/kcore",
                "/proc/keys",
                "/proc/latency_stats",
                "/proc/timer_list",
                "/proc/timer_stats",
                "/proc/sched_debug",
                "/sys/firmware",
                "/proc/scsi",
            ],
            "readonlyPaths": [
                "/proc/bus",
                "/proc/fs",
                "/proc/irq",
                "/proc/sys",
                "/proc/sysrq-trigger",
            ],
        },
        "hooks": {"createContainer": [{"path": "/kind/bin/mount-product-files.sh"}]},
    }
    return json.dumps(spec, indent=2)


# Keep old name as alias for backward compatibility
def generate_cri_base_json():
    """Deprecated: Use generate_high_memlock_spec_json() instead."""
    return generate_high_memlock_spec_json()


def _generate_containerd_config_patches(
    deployment_dir: Path, has_high_memlock: bool
) -> str:
    """Generate containerdConfigPatches YAML for custom runtime handlers.

    This configures containerd to have a runtime handler named 'high-memlock'
    that uses a custom OCI base spec with unlimited RLIMIT_MEMLOCK.
    """
    if not has_high_memlock:
        return ""

    spec_path = deployment_dir.joinpath(constants.high_memlock_spec_filename).resolve()
    runtime_name = constants.high_memlock_runtime
    plugin_path = 'plugins."io.containerd.grpc.v1.cri".containerd.runtimes'
    return (
        "containerdConfigPatches:\n"
        "  - |-\n"
        f"    [{plugin_path}.{runtime_name}]\n"
        '      runtime_type = "io.containerd.runc.v2"\n'
        f'      base_runtime_spec = "{spec_path}"\n'
    )


# Note: this makes any duplicate definition in b overwrite a
def merge_envs(a: Mapping[str, str], b: Mapping[str, str]) -> Mapping[str, str]:
    result = {**a, **b}
    return result


def _expand_shell_vars(
    raw_val: str, env_map: Optional[Mapping[str, str]] = None
) -> str:
    # Expand docker-compose style variable substitution:
    # ${VAR} - use VAR value or empty string
    # ${VAR:-default} - use VAR value or default if unset/empty
    # ${VAR-default} - use VAR value or default if unset
    if env_map is None:
        env_map = {}
    if raw_val is None:
        return ""
    match = re.search(r"^\$\{([^}]+)\}$", raw_val)
    if match:
        inner = match.group(1)
        # Check for default value syntax
        if ":-" in inner:
            var_name, default_val = inner.split(":-", 1)
            return env_map.get(var_name, "") or default_val
        elif "-" in inner:
            var_name, default_val = inner.split("-", 1)
            return env_map.get(var_name, default_val)
        else:
            return env_map.get(inner, "")
    return raw_val


def envs_from_compose_file(
    compose_file_envs: Mapping[str, str], env_map: Optional[Mapping[str, str]] = None
) -> Mapping[str, str]:
    result = {}
    for env_var, env_val in compose_file_envs.items():
        expanded_env_val = _expand_shell_vars(env_val, env_map)
        result.update({env_var: expanded_env_val})
    return result


def translate_sidecar_service_names(
    envs: Mapping[str, str], sibling_service_names: List[str]
) -> Mapping[str, str]:
    """Translate docker-compose service names to localhost for sidecar containers.

    In docker-compose, services can reference each other by name (e.g., 'db:5432').
    In Kubernetes, when multiple containers are in the same pod (sidecars), they
    share the same network namespace and must use 'localhost' instead.

    This function replaces service name references with 'localhost' in env values.
    """
    import re

    if not sibling_service_names:
        return envs

    result = {}
    for env_var, env_val in envs.items():
        if env_val is None:
            result[env_var] = env_val
            continue

        new_val = str(env_val)
        for service_name in sibling_service_names:
            # Match service name followed by optional port (e.g., 'db:5432', 'db')
            # Handle URLs like: postgres://user:pass@db:5432/dbname
            # and simple refs like: db:5432 or just db
            pattern = rf"\b{re.escape(service_name)}(:\d+)?\b"
            new_val = re.sub(pattern, lambda m: f'localhost{m.group(1) or ""}', new_val)

        result[env_var] = new_val

    return result


def envs_from_environment_variables_map(
    map: Mapping[str, str],
) -> List[client.V1EnvVar]:
    result = []
    for env_var, env_val in map.items():
        result.append(client.V1EnvVar(env_var, env_val))
    return result


# This needs to know:
# The service ports for the cluster
# The bind mounted volumes for the cluster
#
# Make ports like this:
#  extraPortMappings:
#  - containerPort: 80
#    hostPort: 80
#    # optional: set the bind address on the host
#    # 0.0.0.0 is the current default
#    listenAddress: "127.0.0.1"
#    # optional: set the protocol to one of TCP, UDP, SCTP.
#    # TCP is the default
#    protocol: TCP
# Make bind mounts like this:
#  extraMounts:
#  - hostPath: /path/to/my/files
#    containerPath: /files
def generate_kind_config(deployment_dir: Path, deployment_context):
    compose_file_dir = deployment_dir.joinpath("compose")
    # TODO: this should come from the stack file, not this way
    pod_files = [p for p in compose_file_dir.iterdir() if p.is_file()]
    parsed_pod_files_map = parsed_pod_files_map_from_file_names(pod_files)
    port_mappings_yml = _generate_kind_port_mappings(parsed_pod_files_map)
    mounts_yml = _generate_kind_mounts(
        parsed_pod_files_map, deployment_dir, deployment_context
    )

    # Check if unlimited_memlock is enabled
    unlimited_memlock = deployment_context.spec.get_unlimited_memlock()

    # Generate containerdConfigPatches for RuntimeClass support
    containerd_patches_yml = _generate_containerd_config_patches(
        deployment_dir, unlimited_memlock
    )

    # Add high-memlock spec file mount if needed
    if unlimited_memlock:
        spec_mount = _generate_high_memlock_spec_mount(deployment_dir)
        if mounts_yml:
            # Append to existing mounts
            mounts_yml = mounts_yml.rstrip() + "\n" + spec_mount
        else:
            mounts_yml = f"  extraMounts:\n{spec_mount}"

    # Build the config - containerdConfigPatches must be at cluster level (before nodes)
    config = "kind: Cluster\n" "apiVersion: kind.x-k8s.io/v1alpha4\n"

    if containerd_patches_yml:
        config += containerd_patches_yml

    config += (
        "nodes:\n"
        "- role: control-plane\n"
        "  kubeadmConfigPatches:\n"
        "    - |\n"
        "      kind: InitConfiguration\n"
        "      nodeRegistration:\n"
        "        kubeletExtraArgs:\n"
        '          node-labels: "ingress-ready=true"\n'
        f"{port_mappings_yml}\n"
        f"{mounts_yml}\n"
    )

    return config
