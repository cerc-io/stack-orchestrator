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
from app.util import get_yaml


class Spec:

    obj: typing.Any

    def __init__(self) -> None:
        pass

    def init_from_file(self, file_path: Path):
        with file_path:
            self.obj = get_yaml().load(open(file_path, "r"))
