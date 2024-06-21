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

import click
from importlib import resources, metadata


@click.command()
@click.pass_context
def command(ctx):
    '''print tool version'''

    # See: https://stackoverflow.com/a/20885799/1701505
    from stack_orchestrator import data
    if resources.is_resource(data, "build_tag.txt"):
        with resources.open_text(data, "build_tag.txt") as version_file:
            # TODO: code better version that skips comment lines
            version_string = version_file.read().splitlines()[1]
    else:
        version_string = metadata.version("laconic-stack-orchestrator") + "-unknown"

    print(version_string)
