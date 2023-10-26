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

from typing import Any, List, Set

from app.opts import opts
from app.util import get_yaml


class ClusterInfo:
    parsed_pod_yaml_map: Any = {}
    image_set: Set[str] = set()

    def __init__(self) -> None:
        pass

    def int_from_pod_files(self, pod_files: List[str]):
        for pod_file in pod_files:
            with open(pod_file, "r") as pod_file_descriptor:
                parsed_pod_file = get_yaml().load(pod_file_descriptor)
                self.parsed_pod_yaml_map[pod_file] = parsed_pod_file
        if opts.o.debug:
            print(f"parsed_pod_yaml_map: {self.parsed_pod_yaml_map}")
        # Find the set of images in the pods
        for pod_name in self.parsed_pod_yaml_map:
            pod = self.parsed_pod_yaml_map[pod_name]
            services = pod["services"]
            for service_name in services:
                service_info = services[service_name]
                image = service_info["image"]
                self.image_set.add(image)
        if opts.o.debug:
            print(f"image_set: {self.image_set}")
