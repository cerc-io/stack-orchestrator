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

def get_stack(config, stack):
    return base_stack(config, stack)


class base_stack():

    def __init__(self, config, stack):
        self.config = config
        self.stack = stack

    def ensure_available(self):
        if self.config.verbose:
            print(f"Checking that base stack {self.stack} is available")
        return 1

    def get_url(self):
        return "http://gitea.local:3000/api/packages/cerc-io/npm/"

# TODO: finish this implementation for the npm package registry