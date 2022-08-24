# Copyright © 2022 Cerc

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

from .app import setup_repositories
from .app import build_containers
from .app import deploy_system

@click.group()
def main_command_group():
    pass

main_command_group.add_command(setup_repositories.command)
main_command_group.add_command(build_containers.command)
main_command_group.add_command(deploy_system.command)
