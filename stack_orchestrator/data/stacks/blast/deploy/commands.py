from pathlib import Path
from shutil import copy


def create(context, extra_args):
    #Our goal here is just to copy the genesis.json file for blast
    deployment_config_dir = context.deployment_dir.joinpath("data", "blast-data")
    command_context = extra_args[2]
    compose_file = [f for f in command_context.cluster_context.compose_files if "blast" in f][0]
    source_config_file = Path(compose_file).parent.parent.joinpath("config", "blast", "genesis.json")
    copy(source_config_file, deployment_config_dir)
