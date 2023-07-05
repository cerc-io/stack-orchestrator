# Copyright © 2022, 2023 Cerc

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

from app.util import get_yaml

default_spec_file_content = """config:
    node_moniker: my-node-name
    chain_id: my-chain-id
"""

init_help_text = """Add helpful text here on setting config variables.
"""


def init(ctx):
    print(init_help_text)
    yaml = get_yaml()
    return yaml.parse(default_spec_file_content)
