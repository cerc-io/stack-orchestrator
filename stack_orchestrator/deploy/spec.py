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
import humanfriendly

from pathlib import Path

from stack_orchestrator.util import get_yaml
from stack_orchestrator import constants


class ResourceLimits:
    cpus: float = None
    memory: int = None
    storage: int = None

    def __init__(self, obj={}):
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
    limits: ResourceLimits = None
    reservations: ResourceLimits = None

    def __init__(self, obj={}):
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

    obj: typing.Any
    file_path: Path

    def __init__(self) -> None:
        pass

    def init_from_file(self, file_path: Path):
        with file_path:
            self.obj = get_yaml().load(open(file_path, "r"))
            self.file_path = file_path

    def get_image_registry(self):
        return (self.obj[constants.image_resigtry_key]
                if self.obj and constants.image_resigtry_key in self.obj
                else None)

    def get_volumes(self):
        return (self.obj["volumes"]
                if self.obj and "volumes" in self.obj
                else {})

    def get_configmaps(self):
        return (self.obj["configmaps"]
                if self.obj and "configmaps" in self.obj
                else {})

    def get_container_resources(self):
        return Resources(self.obj.get("resources", {}).get("containers", {}))

    def get_volume_resources(self):
        return Resources(self.obj.get("resources", {}).get("volumes", {}))

    def get_http_proxy(self):
        return (self.obj[constants.network_key][constants.http_proxy_key]
                if self.obj and constants.network_key in self.obj
                and constants.http_proxy_key in self.obj[constants.network_key]
                else None)

    def get_annotations(self):
        return self.obj.get("annotations", {})

    def get_labels(self):
        return self.obj.get("labels", {})

    def get_privileged(self):
        return "true" == str(self.obj.get("security", {}).get("privileged", "false")).lower()

    def get_capabilities(self):
        return self.obj.get("security", {}).get("capabilities", [])
