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

from decouple import config
import os.path
import sys
import ruamel.yaml
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


def get_stack_file_path(stack):
    # In order to be compatible with Python 3.8 we need to use this hack to get the path:
    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    stack_file_path = Path(__file__).absolute().parent.joinpath("data", "stacks", stack, "stack.yml")
    return stack_file_path


def get_dev_root_path(ctx):
    if ctx and ctx.local_stack:
        # TODO: This code probably doesn't work
        dev_root_path = os.getcwd()[0:os.getcwd().rindex("stack-orchestrator")]
        print(f'Local stack dev_root_path (CERC_REPO_BASE_DIR) overridden to: {dev_root_path}')
    else:
        dev_root_path = os.path.expanduser(config("CERC_REPO_BASE_DIR", default="~/cerc"))
    return dev_root_path


# Caller can pass either the name of a stack, or a path to a stack file
def get_parsed_stack_config(stack):
    stack_file_path = stack if isinstance(stack, os.PathLike) else get_stack_file_path(stack)
    try:
        with stack_file_path:
            stack_config = get_yaml().load(open(stack_file_path, "r"))
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


def get_pod_list(parsed_stack):
    # Handle both old and new format
    pods = parsed_stack["pods"]
    if type(pods[0]) is str:
        result = pods
    else:
        result = []
        for pod in pods:
            result.append(pod["name"])
    return result


def get_pod_file_path(parsed_stack, pod_name: str):
    pods = parsed_stack["pods"]
    if type(pods[0]) is str:
        result = os.path.join(get_compose_file_dir(), f"docker-compose-{pod_name}.yml")
    else:
        for pod in pods:
            if pod["name"] == pod_name:
                pod_root_dir = os.path.join(get_dev_root_path(None), pod["repository"].split("/")[-1], pod["path"])
                result = os.path.join(pod_root_dir, "docker-compose.yml")
    return result


def get_pod_script_paths(parsed_stack, pod_name: str):
    pods = parsed_stack["pods"]
    result = []
    if not type(pods[0]) is str:
        for pod in pods:
            if pod["name"] == pod_name:
                pod_root_dir = os.path.join(get_dev_root_path(None), pod["repository"].split("/")[-1], pod["path"])
                if "pre_start_command" in pod:
                    result.append(os.path.join(pod_root_dir, pod["pre_start_command"]))
                if "post_start_command" in pod:
                    result.append(os.path.join(pod_root_dir, pod["post_start_command"]))
    return result


def pod_has_scripts(parsed_stack, pod_name: str):
    pods = parsed_stack["pods"]
    if type(pods[0]) is str:
        result = False
    else:
        for pod in pods:
            if pod["name"] == pod_name:
                result = "pre_start_command" in pod or "post_start_command" in pod
    return result


def get_compose_file_dir():
    # TODO: refactor to use common code with deploy command
    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    data_dir = Path(__file__).absolute().parent.joinpath("data")
    source_compose_dir = data_dir.joinpath("compose")
    return source_compose_dir


def get_parsed_deployment_spec(spec_file):
    spec_file_path = Path(spec_file)
    try:
        with spec_file_path:
            deploy_spec = get_yaml().load(open(spec_file_path, "r"))
            return deploy_spec
    except FileNotFoundError as error:
        # We try here to generate a useful diagnostic error
        print(f"Error: spec file: {spec_file_path} does not exist")
        print(f"Exiting, error: {error}")
        sys.exit(1)


def get_yaml():
    # See: https://stackoverflow.com/a/45701840/1701505
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.indent(sequence=3, offset=1)
    return yaml


# TODO: this is fragile wrt to the subcommand depth
# See also: https://github.com/pallets/click/issues/108
def global_options(ctx):
    return ctx.parent.parent.obj


# TODO: hack
def global_options2(ctx):
    return ctx.parent.obj
