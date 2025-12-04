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
from dotenv import dotenv_values
from typing import Mapping, Set, List
from stack_orchestrator.constants import stack_file_name, deployment_file_name


def include_exclude_check(s, include, exclude):
    if include is None and exclude is None:
        return True
    if include is not None:
        include_list = include.split(",")
        return s in include_list
    if exclude is not None:
        exclude_list = exclude.split(",")
        return s not in exclude_list


def get_stack_path(stack):
    if stack_is_external(stack):
        stack_path = Path(stack)
    else:
        # In order to be compatible with Python 3.8 we need to use this hack to get the path:
        # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
        stack_path = Path(__file__).absolute().parent.joinpath("data", "stacks", stack)
    return stack_path


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
    stack_file_path = get_stack_path(stack).joinpath(stack_file_name)
    if stack_file_path.exists():
        return get_yaml().load(open(stack_file_path, "r"))
    # We try here to generate a useful diagnostic error
    # First check if the stack directory is present
    if stack_file_path.parent.exists():
        error_exit(f"stack.yml file is missing from stack: {stack}")
    error_exit(f"stack {stack} does not exist")


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


def get_job_list(parsed_stack):
    # Return list of jobs from stack config, or empty list if no jobs defined
    if "jobs" not in parsed_stack:
        return []
    jobs = parsed_stack["jobs"]
    if not jobs:
        return []
    if type(jobs[0]) is str:
        result = jobs
    else:
        result = []
        for job in jobs:
            result.append(job["name"])
    return result


def get_plugin_code_paths(stack) -> List[Path]:
    parsed_stack = get_parsed_stack_config(stack)
    pods = parsed_stack["pods"]
    result: Set[Path] = set()
    for pod in pods:
        if type(pod) is str:
            result.add(get_stack_path(stack))
        else:
            pod_root_dir = os.path.join(get_dev_root_path(None), pod["repository"].split("/")[-1], pod["path"])
            result.add(Path(os.path.join(pod_root_dir, "stack")))
    return list(result)


# # Find a config directory, looking first in any external stack
# and if not found there, internally
def resolve_config_dir(stack, config_dir_name: str):
    if stack_is_external(stack):
        # First try looking in the external stack for the compose file
        config_base = Path(stack).parent.parent.joinpath("config")
        proposed_dir = config_base.joinpath(config_dir_name)
        if proposed_dir.exists():
            return proposed_dir
        # If we don't find it fall through to the internal case
    config_base = get_internal_config_dir()
    return config_base.joinpath(config_dir_name)


# Find a compose file, looking first in any external stack
# and if not found there, internally
def resolve_compose_file(stack, pod_name: str):
    if stack_is_external(stack):
        # First try looking in the external stack for the compose file
        compose_base = Path(stack).parent.parent.joinpath("compose")
        proposed_file = compose_base.joinpath(f"docker-compose-{pod_name}.yml")
        if proposed_file.exists():
            return proposed_file
        # If we don't find it fall through to the internal case
    compose_base = get_internal_compose_file_dir()
    return compose_base.joinpath(f"docker-compose-{pod_name}.yml")


# Find a job compose file in compose-jobs directory
def resolve_job_compose_file(stack, job_name: str):
    if stack_is_external(stack):
        # First try looking in the external stack for the job compose file
        compose_jobs_base = Path(stack).parent.parent.joinpath("compose-jobs")
        proposed_file = compose_jobs_base.joinpath(f"docker-compose-{job_name}.yml")
        if proposed_file.exists():
            return proposed_file
        # If we don't find it fall through to the internal case
    # TODO: Add internal compose-jobs directory support if needed
    # For now, jobs are expected to be in external stacks only
    compose_jobs_base = Path(stack).parent.parent.joinpath("compose-jobs")
    return compose_jobs_base.joinpath(f"docker-compose-{job_name}.yml")


def get_pod_file_path(stack, parsed_stack, pod_name: str):
    pods = parsed_stack["pods"]
    if type(pods[0]) is str:
        result = resolve_compose_file(stack, pod_name)
    else:
        for pod in pods:
            if pod["name"] == pod_name:
                pod_root_dir = os.path.join(get_dev_root_path(None), pod["repository"].split("/")[-1], pod["path"])
                result = os.path.join(pod_root_dir, "docker-compose.yml")
    return result


def get_job_file_path(stack, parsed_stack, job_name: str):
    if "jobs" not in parsed_stack or not parsed_stack["jobs"]:
        return None
    jobs = parsed_stack["jobs"]
    if type(jobs[0]) is str:
        result = resolve_job_compose_file(stack, job_name)
    else:
        # TODO: Support complex job definitions if needed
        result = resolve_job_compose_file(stack, job_name)
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


def get_internal_compose_file_dir():
    # TODO: refactor to use common code with deploy command
    # See: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure
    data_dir = Path(__file__).absolute().parent.joinpath("data")
    source_compose_dir = data_dir.joinpath("compose")
    return source_compose_dir


def get_internal_config_dir():
    # TODO: refactor to use common code with deploy command
    data_dir = Path(__file__).absolute().parent.joinpath("data")
    source_config_dir = data_dir.joinpath("config")
    return source_config_dir


def get_k8s_dir():
    data_dir = Path(__file__).absolute().parent.joinpath("data")
    source_config_dir = data_dir.joinpath("k8s")
    return source_config_dir


def get_parsed_deployment_spec(spec_file):
    spec_file_path = Path(spec_file)
    try:
        return get_yaml().load(open(spec_file_path, "r"))
    except FileNotFoundError as error:
        # We try here to generate a useful diagnostic error
        print(f"Error: spec file: {spec_file_path} does not exist")
        print(f"Exiting, error: {error}")
        sys.exit(1)


def stack_is_external(stack: str):
    # Bit of a hack: if the supplied stack string represents
    # a path that exists then we assume it must be external
    return Path(stack).exists() if stack is not None else False


def stack_is_in_deployment(stack: Path):
    if isinstance(stack, os.PathLike):
        return stack.joinpath(deployment_file_name).exists()
    else:
        return False


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


def error_exit(s):
    print(f"ERROR: {s}")
    sys.exit(1)


def warn_exit(s):
    print(f"WARN: {s}")
    sys.exit(0)


def env_var_map_from_file(file: Path) -> Mapping[str, str]:
    return dotenv_values(file)
