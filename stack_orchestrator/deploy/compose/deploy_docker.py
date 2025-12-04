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

from pathlib import Path
from python_on_whales import DockerClient, DockerException
from stack_orchestrator.deploy.deployer import Deployer, DeployerException, DeployerConfigGenerator
from stack_orchestrator.deploy.deployment_context import DeploymentContext
from stack_orchestrator.opts import opts


class DockerDeployer(Deployer):
    name: str = "compose"
    type: str

    def __init__(self, type, deployment_context: DeploymentContext, compose_files, compose_project_name, compose_env_file) -> None:
        self.docker = DockerClient(compose_files=compose_files, compose_project_name=compose_project_name,
                                   compose_env_file=compose_env_file)
        self.type = type

    def up(self, detach, skip_cluster_management, services):
        if not opts.o.dry_run:
            try:
                return self.docker.compose.up(detach=detach, services=services)
            except DockerException as e:
                raise DeployerException(e)

    def down(self, timeout, volumes, skip_cluster_management):
        if not opts.o.dry_run:
            try:
                return self.docker.compose.down(timeout=timeout, volumes=volumes)
            except DockerException as e:
                raise DeployerException(e)

    def update(self):
        if not opts.o.dry_run:
            try:
                return self.docker.compose.restart()
            except DockerException as e:
                raise DeployerException(e)

    def status(self):
        if not opts.o.dry_run:
            try:
                for p in self.docker.compose.ps():
                    print(f"{p.name}\t{p.state.status}")
            except DockerException as e:
                raise DeployerException(e)

    def ps(self):
        if not opts.o.dry_run:
            try:
                return self.docker.compose.ps()
            except DockerException as e:
                raise DeployerException(e)

    def port(self, service, private_port):
        if not opts.o.dry_run:
            try:
                return self.docker.compose.port(service=service, private_port=private_port)
            except DockerException as e:
                raise DeployerException(e)

    def execute(self, service, command, tty, envs):
        if not opts.o.dry_run:
            try:
                return self.docker.compose.execute(service=service, command=command, tty=tty, envs=envs)
            except DockerException as e:
                raise DeployerException(e)

    def logs(self, services, tail, follow, stream):
        if not opts.o.dry_run:
            try:
                return self.docker.compose.logs(services=services, tail=tail, follow=follow, stream=stream)
            except DockerException as e:
                raise DeployerException(e)

    def run(self, image: str, command=None, user=None, volumes=None, entrypoint=None, env={}, ports=[], detach=False):
        if not opts.o.dry_run:
            try:
                return self.docker.run(image=image, command=command, user=user, volumes=volumes,
                                       entrypoint=entrypoint, envs=env, detach=detach, publish=ports, publish_all=len(ports) == 0)
            except DockerException as e:
                raise DeployerException(e)

    def run_job(self, job_name: str, release_name: str = None):
        # release_name is ignored for Docker deployments (only used for K8s/Helm)
        if not opts.o.dry_run:
            try:
                # Find job compose file in compose-jobs directory
                # The deployment should have compose-jobs/docker-compose-<job_name>.yml
                if not self.docker.compose_files:
                    raise DeployerException("No compose files configured")

                # Deployment directory is parent of compose directory
                compose_dir = Path(self.docker.compose_files[0]).parent
                deployment_dir = compose_dir.parent
                job_compose_file = deployment_dir / "compose-jobs" / f"docker-compose-{job_name}.yml"

                if not job_compose_file.exists():
                    raise DeployerException(f"Job compose file not found: {job_compose_file}")

                if opts.o.verbose:
                    print(f"Running job from: {job_compose_file}")

                # Create a DockerClient for the job compose file with same project name and env file
                # This allows the job to access volumes from the main deployment
                job_docker = DockerClient(
                    compose_files=[job_compose_file],
                    compose_project_name=self.docker.compose_project_name,
                    compose_env_file=self.docker.compose_env_file
                )

                # Run the job with --rm flag to remove container after completion
                return job_docker.compose.run(service=job_name, remove=True, tty=True)

            except DockerException as e:
                raise DeployerException(e)


class DockerDeployerConfigGenerator(DeployerConfigGenerator):

    def __init__(self, type: str) -> None:
        super().__init__()

    # Nothing needed at present for the docker deployer
    def generate(self, deployment_dir: Path):
        pass
