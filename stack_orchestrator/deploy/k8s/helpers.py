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
import os
from pathlib import Path
import subprocess
import re
from typing import Set, Mapping, List, Optional, cast

from stack_orchestrator.util import get_k8s_dir, error_exit
from stack_orchestrator.opts import opts
from stack_orchestrator.deploy.deploy_util import parsed_pod_files_map_from_file_names
from stack_orchestrator.deploy.deployer import DeployerException
from stack_orchestrator import constants


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


def create_cluster(name: str, config_file: str):
    result = _run_command(f"kind create cluster --name {name} --config {config_file}")
    if result.returncode != 0:
        raise DeployerException(f"kind create cluster failed: {result}")


def destroy_cluster(name: str):
    _run_command(f"kind delete cluster --name {name}")


def wait_for_ingress_in_kind():
    core_v1 = client.CoreV1Api()
    for i in range(20):
        warned_waiting = False
        w = watch.Watch()
        for event in w.stream(
            func=core_v1.list_namespaced_pod,
            namespace="ingress-nginx",
            label_selector="app.kubernetes.io/component=controller",
            timeout_seconds=30,
        ):
            event_dict = cast(dict, event)
            pod = cast(client.V1Pod, event_dict.get("object"))
            if pod and pod.status and pod.status.container_statuses:
                if pod.status.container_statuses[0].ready is True:
                    if warned_waiting:
                        print("Ingress controller is ready")
                    return
            print("Waiting for ingress controller to become ready...")
            warned_waiting = True
    error_exit("ERROR: Timed out waiting for ingress to become ready")


def install_ingress_for_kind():
    api_client = client.ApiClient()
    ingress_install = os.path.abspath(
        get_k8s_dir().joinpath(
            "components", "ingress", "ingress-nginx-kind-deploy.yaml"
        )
    )
    if opts.o.debug:
        print("Installing nginx ingress controller in kind cluster")
    utils.create_from_yaml(api_client, yaml_file=ingress_install)


def load_images_into_kind(kind_cluster_name: str, image_set: Set[str]):
    for image in image_set:
        result = _run_command(
            f"kind load docker-image {image} --name {kind_cluster_name}"
        )
        if result.returncode != 0:
            raise DeployerException(f"kind load docker-image failed: {result}")


def pods_in_deployment(core_api: client.CoreV1Api, deployment_name: str):
    pods = []
    pod_response = core_api.list_namespaced_pod(
        namespace="default", label_selector=f"app={deployment_name}"
    )
    if opts.o.debug:
        print(f"pod_response: {pod_response}")
    for pod_info in pod_response.items:
        pod_name = pod_info.metadata.name
        pods.append(pod_name)
    return pods


def containers_in_pod(core_api: client.CoreV1Api, pod_name: str) -> List[str]:
    containers: List[str] = []
    pod_response = cast(
        client.V1Pod, core_api.read_namespaced_pod(pod_name, namespace="default")
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


def get_kind_pv_bind_mount_path(volume_name: str):
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
                            if opts.o.debug:
                                print(f"mount_string: {mount_string}")
                            mount_split = mount_string.split(":")
                            volume_name = mount_split[0]
                            mount_path = mount_split[1]
                            mount_options = (
                                mount_split[2] if len(mount_split) == 3 else None
                            )
                            if opts.o.debug:
                                print(f"volume_name: {volume_name}")
                                print(f"mount path: {mount_path}")
                                print(f"mount options: {mount_options}")
                            volume_device = client.V1VolumeMount(
                                mount_path=mount_path,
                                name=volume_name,
                                read_only="ro" == mount_options,
                            )
                            result.append(volume_device)
    return result


def volumes_for_pod_files(parsed_pod_files, spec, app_name):
    result = []
    for pod in parsed_pod_files:
        parsed_pod_file = parsed_pod_files[pod]
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
                        if opts.o.debug:
                            print(f"mount_string: {mount_string}")
                        mount_split = mount_string.split(":")
                        volume_name = mount_split[0]
                        mount_path = mount_split[1]
                        if opts.o.debug:
                            print(f"volume_name: {volume_name}")
                            print(f"map: {volume_host_path_map}")
                            print(f"mount path: {mount_path}")
                        if volume_name not in deployment_context.spec.get_configmaps():
                            if volume_host_path_map[volume_name]:
                                host_path = _make_absolute_host_path(
                                    volume_host_path_map[volume_name],
                                    deployment_dir,
                                )
                                container_path = get_kind_pv_bind_mount_path(
                                    volume_name
                                )
                                volume_definitions.append(
                                    f"  - hostPath: {host_path}\n"
                                    f"    containerPath: {container_path}\n"
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
    # For now we just map port 80 for the nginx ingress controller we install in kind
    port_string = "80"
    port_definitions.append(
        f"  - containerPort: {port_string}\n    hostPort: {port_string}\n"
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
    return f"  - hostPath: {spec_path}\n" f"    containerPath: {spec_path}\n"


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


def envs_from_environment_variables_map(
    map: Mapping[str, str]
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
