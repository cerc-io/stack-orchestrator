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

import os.path
import sys
import yaml
from pathlib import Path


def include_exclude_check(s, include, exclude):
    if include is None and exclude is None:
        return True
    if include is not None:
        include_list = include.split(",")
        return s in include_list
    if exclude is not None:
        exclude_list = exclude.split(",")
        return s not in exclude_list


def get_parsed_stack_config(stack):
    # In order to be compatible with Python 3.8 we need to use this hack to get the path:
    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    stack_file_path = Path(__file__).absolute().parent.joinpath("data", "stacks", stack, "stack.yml")
    try:
        with stack_file_path:
            stack_config = yaml.safe_load(open(stack_file_path, "r"))
            return stack_config
    except FileNotFoundError as error:
        # We try here to generate a useful diagnostic error
        # First check if the stack directory is present
        stack_directory = stack_file_path.parent
        if os.path.exists(stack_directory):
            print(f"Error: stack.yml file is missing from stack: {stack}")
        else:
            print(f"Error: stack: {stack} does not exist")
        print(f"Exiting, error: {error}")
        sys.exit(1)
