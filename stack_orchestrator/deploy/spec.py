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

from pathlib import Path
import typing
from stack_orchestrator.util import get_yaml
from stack_orchestrator import constants


class Spec:

    obj: typing.Any

    def __init__(self) -> None:
        pass

    def init_from_file(self, file_path: Path):
        with file_path:
            self.obj = get_yaml().load(open(file_path, "r"))

    def get_image_registry(self):
        return (self.obj[constants.image_resigtry_key]
                if self.obj and constants.image_resigtry_key in self.obj
                else None)

    def get_http_proxy(self):
        return (self.obj[constants.network_key][constants.http_proxy_key]
                if self.obj and constants.network_key in self.obj
                and constants.http_proxy_key in self.obj[constants.network_key]
                else None)
