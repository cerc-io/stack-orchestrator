from testcontainers.compose import DockerCompose
from testcontainers.core.docker_client import DockerClient
from testcontainers.core.exceptions import NoSuchPortExposed
from testcontainers.core.waiting_utils import wait_for_logs

with DockerCompose(filepath=".", compose_file_name="docker-compose-test.yaml") as compose:
    port = compose.get_service_port("db", 5432)
    print(port)
