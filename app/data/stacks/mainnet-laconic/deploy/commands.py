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

import click
import os
from shutil import copyfile
import sys
from .util import get_stack_config_filename, get_parsed_deployment_spec

default_spec_file_content = """stack: mainnet-laconic
data_dir: /my/path
node_name: my-node-name
"""


def make_default_deployment_dir():
    return "deployment-001"

@click.command()
@click.option("--output", required=True, help="Write yaml spec file here")
@click.pass_context
def init(ctx, output):
    with open(output, "w") as output_file:
        output_file.write(default_spec_file_content)


@click.command()
@click.option("--spec-file", required=True, help="Spec file to use to create this deployment")
@click.option("--deployment-dir", help="Create deployment files in this directory")
@click.pass_context
def create(ctx, spec_file, deployment_dir):
    # This function fails with a useful error message if the file doens't exist
    parsed_spec = get_parsed_deployment_spec(spec_file)
    if ctx.debug:
        print(f"parsed spec: {parsed_spec}")
    if deployment_dir is None:
        deployment_dir = make_default_deployment_dir()
    if os.path.exists(deployment_dir):
        print(f"Error: {deployment_dir} already exists")
        sys.exit(1)
    os.mkdir(deployment_dir)
    # Copy spec file and the stack file into the deployment dir
    copyfile(spec_file, os.path.join(deployment_dir, os.path.basename(spec_file)))
    stack_file = get_stack_config_filename(parsed_spec.stack)
    copyfile(stack_file, os.path.join(deployment_dir, os.path.basename(stack_file)))
