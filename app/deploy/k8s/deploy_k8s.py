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

from kubernetes import client, config

from app.deploy.deployer import Deployer
from app.deploy.k8s.helpers import create_cluster, destroy_cluster, load_images_into_kind
from app.deploy.k8s.cluster_info import ClusterInfo
from app.opts import opts


class K8sDeployer(Deployer):
    name: str = "k8s"
    k8s_client: client
    kind_cluster_name: str
    cluster_info : ClusterInfo

    def __init__(self, compose_files, compose_project_name, compose_env_file) -> None:
        if (opts.o.debug):
            print(f"Compose files: {compose_files}")
            print(f"Project name: {compose_project_name}")
            print(f"Env file: {compose_env_file}")
        self.kind_cluster_name = compose_project_name
        self.cluster_info = ClusterInfo()
        self.cluster_info.int_from_pod_files(compose_files)

    def connect_api(self):
        config.load_kube_config(context=f"kind-{self.kind_cluster_name}")
        self.k8s_client = client.CoreV1Api()
        self.k8s_api = client.AppsV1Api()

    def up(self, detach, services):
        # Create the kind cluster
        create_cluster(self.kind_cluster_name)
        self.connect_api()
        # Ensure the referenced containers are copied into kind
        load_images_into_kind(self.kind_cluster_name, self.cluster_info.image_set)
        # Process compose files into a Deployment
        deployment = self.cluster_info.get_deployment()
        # Create the k8s objects
        resp = self.k8s_api.create_namespaced_deployment(
            body=deployment, namespace="default"
        )

        if opts.o.debug:
            print("Deployment created.\n")
            print(f"{resp.metadata.namespace} {resp.metadata.name} \
                  {resp.metadata.generation} {resp.spec.template.spec.containers[0].image}")

    def down(self, timeout, volumes):
        # Delete the k8s objects
        # Destroy the kind cluster
        destroy_cluster(self.kind_cluster_name)

    def ps(self):
        self.connect_api()
        # Call whatever API we need to get the running container list
        ret = self.k8s_client.list_pod_for_all_namespaces(watch=False)
        if ret.items:
            for i in ret.items:
                print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        ret = self.k8s_client.list_node(pretty=True, watch=False)
        return []

    def port(self, service, private_port):
        # Since we handle the port mapping, need to figure out where this comes from
        # Also look into whether it makes sense to get ports for k8s
        pass

    def execute(self, service_name, command, envs):
        # Call the API to execute a command in a running container
        pass

    def logs(self, services, tail, follow, stream):
        # Call the API to get logs
        pass

    def run(self, image, command, user, volumes, entrypoint=None):
        # We need to figure out how to do this -- check why we're being called first
        pass
