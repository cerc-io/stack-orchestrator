# Copyright © 2024 Vulcanize

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

import importlib.resources

from stack_orchestrator.opts import opts
from stack_orchestrator.util import get_parsed_stack_config, warn_exit


def get_containers_in_scope(stack: str):
    containers_in_scope = []
    if stack:
        stack_config = get_parsed_stack_config(stack)
        if "containers" not in stack_config or stack_config["containers"] is None:
            warn_exit(f"stack {stack} does not define any containers")
        containers_in_scope = stack_config["containers"]
    else:
        # See: https://stackoverflow.com/a/20885799/1701505
        from stack_orchestrator import data

        with importlib.resources.open_text(
            data, "container-image-list.txt"
        ) as container_list_file:
            containers_in_scope = container_list_file.read().splitlines()

    if opts.o.verbose:
        print(f"Containers: {containers_in_scope}")
        if stack:
            print(f"Stack: {stack}")

    return containers_in_scope
