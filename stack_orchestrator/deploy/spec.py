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

import typing
from typing import Optional
import humanfriendly

from pathlib import Path

from stack_orchestrator.util import get_yaml
from stack_orchestrator import constants


class ResourceLimits:
    cpus: Optional[float] = None
    memory: Optional[int] = None
    storage: Optional[int] = None

    def __init__(self, obj=None):
        if obj is None:
            obj = {}
        if "cpus" in obj:
            self.cpus = float(obj["cpus"])
        if "memory" in obj:
            self.memory = humanfriendly.parse_size(obj["memory"])
        if "storage" in obj:
            self.storage = humanfriendly.parse_size(obj["storage"])

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        for k in self.__dict__:
            yield k, self.__dict__[k]

    def __repr__(self):
        return str(self.__dict__)


class Resources:
    limits: Optional[ResourceLimits] = None
    reservations: Optional[ResourceLimits] = None

    def __init__(self, obj=None):
        if obj is None:
            obj = {}
        if "reservations" in obj:
            self.reservations = ResourceLimits(obj["reservations"])
        if "limits" in obj:
            self.limits = ResourceLimits(obj["limits"])

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        for k in self.__dict__:
            yield k, self.__dict__[k]

    def __repr__(self):
        return str(self.__dict__)


class Spec:
    """Deployment spec (spec.yml) — describes WHERE and HOW to deploy a stack.

    A spec.yml contains deployment-specific infrastructure configuration:
      - stack: path to the stack definition
      - deploy-to: target platform (k8s-kind, k8s, compose)
      - network: ports, http-proxy, acme-email
      - resources: CPU/memory limits and reservations
      - security: privileged, capabilities, memlock
      - volumes: host path mappings for persistent data
      - configmaps: directories mounted as k8s ConfigMaps
      - config: deployment-specific env var OVERRIDES (see below)

    The config: section is for deployment-specific values only — things
    that differ between deployments (hostnames, endpoints, secrets).
    Application defaults belong in the compose file's environment section,
    not here. If a value would be the same across all deployments of this
    stack, it belongs in the compose file, not in spec.yml.

    Good config: entries (deployment-specific):
      VALIDATOR_ENTRYPOINT: my-cluster.example.com:8001
      PUBLIC_RPC_ADDRESS: my-node.example.com:8899
      GOSSIP_HOST: 10.0.0.1

    Bad config: entries (these are application defaults):
      RPC_PORT: '8899'          # same everywhere, belongs in compose
      LIMIT_LEDGER_SIZE: '50000000'  # same everywhere, belongs in compose
      RUST_LOG: info             # same everywhere, belongs in compose
    """

    obj: typing.Any
    file_path: Optional[Path]

    def __init__(self, file_path: Optional[Path] = None, obj=None) -> None:
        if obj is None:
            obj = {}
        self.file_path = file_path
        self.obj = obj

    def __getitem__(self, item):
        return self.obj[item]

    def __contains__(self, item):
        return item in self.obj

    def get(self, item, default=None):
        return self.obj.get(item, default)

    def init_from_file(self, file_path: Path):
        self.obj = get_yaml().load(open(file_path, "r"))
        self.file_path = file_path

    def get_image_registry(self):
        return self.obj.get(constants.image_registry_key)

    def get_image_registry_config(self) -> typing.Optional[typing.Dict]:
        """Returns registry auth config: {server, username, token-env}.

        Used for private container registries like GHCR. The token-env field
        specifies an environment variable containing the API token/PAT.

        Note: Uses 'registry-credentials' key to avoid collision with
        'image-registry' key which is for pushing images.
        """
        return self.obj.get("registry-credentials")

    def get_volumes(self):
        return self.obj.get(constants.volumes_key, {})

    def get_configmaps(self):
        return self.obj.get(constants.configmaps_key, {})

    def get_container_resources(self):
        return Resources(
            self.obj.get(constants.resources_key, {}).get("containers", {})
        )

    def get_volume_resources(self):
        return Resources(
            self.obj.get(constants.resources_key, {}).get(constants.volumes_key, {})
        )

    def get_http_proxy(self):
        return self.obj.get(constants.network_key, {}).get(constants.http_proxy_key, [])

    def get_annotations(self):
        return self.obj.get(constants.annotations_key, {})

    def get_replicas(self):
        return self.obj.get(constants.replicas_key, 1)

    def get_node_affinities(self):
        return self.obj.get(constants.node_affinities_key, [])

    def get_node_tolerations(self):
        return self.obj.get(constants.node_tolerations_key, [])

    def get_labels(self):
        return self.obj.get(constants.labels_key, {})

    def get_privileged(self):
        return (
            "true"
            == str(
                self.obj.get(constants.security_key, {}).get("privileged", "false")
            ).lower()
        )

    def get_capabilities(self):
        return self.obj.get(constants.security_key, {}).get("capabilities", [])

    def get_unlimited_memlock(self):
        return (
            "true"
            == str(
                self.obj.get(constants.security_key, {}).get(
                    constants.unlimited_memlock_key, "false"
                )
            ).lower()
        )

    def get_runtime_class(self):
        """Get runtime class name from spec, or derive from security settings.

        The runtime class determines which containerd runtime handler to use,
        allowing different pods to have different rlimit profiles (e.g., for
        unlimited RLIMIT_MEMLOCK).

        Returns:
            Runtime class name string, or None to use default runtime.
        """
        # Explicit runtime class takes precedence
        explicit = self.obj.get(constants.security_key, {}).get(
            constants.runtime_class_key, None
        )
        if explicit:
            return explicit

        # Auto-derive from unlimited-memlock setting
        if self.get_unlimited_memlock():
            return constants.high_memlock_runtime

        return None  # Use default runtime

    def get_deployment_type(self):
        return self.obj.get(constants.deploy_to_key)

    def get_acme_email(self):
        return self.obj.get(constants.network_key, {}).get(constants.acme_email_key, "")

    def is_kubernetes_deployment(self):
        return self.get_deployment_type() in [
            constants.k8s_kind_deploy_type,
            constants.k8s_deploy_type,
        ]

    def is_kind_deployment(self):
        return self.get_deployment_type() in [constants.k8s_kind_deploy_type]

    def get_kind_mount_root(self):
        return self.obj.get(constants.kind_mount_root_key)

    def is_docker_deployment(self):
        return self.get_deployment_type() in [constants.compose_deploy_type]
