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

from pathlib import Path
from kubernetes import client, config

from stack_orchestrator import constants
from stack_orchestrator.deploy.deployer import Deployer, DeployerConfigGenerator
from stack_orchestrator.deploy.k8s.helpers import create_cluster, destroy_cluster, load_images_into_kind
from stack_orchestrator.deploy.k8s.helpers import pods_in_deployment, log_stream_from_string, generate_kind_config
from stack_orchestrator.deploy.k8s.cluster_info import ClusterInfo
from stack_orchestrator.opts import opts


class K8sDeployer(Deployer):
    name: str = "k8s"
    type: str
    core_api: client.CoreV1Api
    apps_api: client.AppsV1Api
    k8s_namespace: str = "default"
    kind_cluster_name: str
    cluster_info : ClusterInfo
    deployment_dir: Path

    def __init__(self, type, deployment_dir, compose_files, compose_project_name, compose_env_file) -> None:
        if (opts.o.debug):
            print(f"Deployment dir: {deployment_dir}")
            print(f"Compose files: {compose_files}")
            print(f"Project name: {compose_project_name}")
            print(f"Env file: {compose_env_file}")
            print(f"Type: {type}")
        self.type = type
        self.deployment_dir = deployment_dir
        self.kind_cluster_name = compose_project_name
        self.cluster_info = ClusterInfo()
        self.cluster_info.int(compose_files, compose_env_file)

    def connect_api(self):
        if self.is_kind():
            config.load_kube_config(context=f"kind-{self.kind_cluster_name}")
        else:
            # Get the config file and pass to load_kube_config()
            config.load_kube_config(config_file=self.deployment_dir.joinpath(constants.kube_config_filename).as_posix())
        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()

    def up(self, detach, services):
        if self.is_kind():
            # Create the kind cluster
            create_cluster(self.kind_cluster_name, self.deployment_dir.joinpath(constants.kind_config_filename))
            # Ensure the referenced containers are copied into kind
            load_images_into_kind(self.kind_cluster_name, self.cluster_info.image_set)
        self.connect_api()

        # Create the host-path-mounted PVs for this deployment
        pvs = self.cluster_info.get_pvs()
        for pv in pvs:
            if opts.o.debug:
                print(f"Sending this pv: {pv}")
            pv_resp = self.core_api.create_persistent_volume(body=pv)
            if opts.o.debug:
                print("PVs created:")
                print(f"{pv_resp}")

        # Figure out the PVCs for this deployment
        pvcs = self.cluster_info.get_pvcs()
        for pvc in pvcs:
            if opts.o.debug:
                print(f"Sending this pvc: {pvc}")
            pvc_resp = self.core_api.create_namespaced_persistent_volume_claim(body=pvc, namespace=self.k8s_namespace)
            if opts.o.debug:
                print("PVCs created:")
                print(f"{pvc_resp}")
        # Process compose files into a Deployment
        deployment = self.cluster_info.get_deployment()
        # Create the k8s objects
        if opts.o.debug:
            print(f"Sending this deployment: {deployment}")
        deployment_resp = self.apps_api.create_namespaced_deployment(
            body=deployment, namespace=self.k8s_namespace
        )
        if opts.o.debug:
            print("Deployment created:")
            print(f"{deployment_resp.metadata.namespace} {deployment_resp.metadata.name} \
                  {deployment_resp.metadata.generation} {deployment_resp.spec.template.spec.containers[0].image}")

    def down(self, timeout, volumes):
        self.connect_api()
        # Delete the k8s objects
        # Create the host-path-mounted PVs for this deployment
        pvs = self.cluster_info.get_pvs()
        for pv in pvs:
            if opts.o.debug:
                print(f"Deleting this pv: {pv}")
            pv_resp = self.core_api.delete_persistent_volume(name=pv.metadata.name)
            if opts.o.debug:
                print("PV deleted:")
                print(f"{pv_resp}")

        # Figure out the PVCs for this deployment
        pvcs = self.cluster_info.get_pvcs()
        for pvc in pvcs:
            if opts.o.debug:
                print(f"Deleting this pvc: {pvc}")
            pvc_resp = self.core_api.delete_namespaced_persistent_volume_claim(name=pvc.metadata.name, namespace=self.k8s_namespace)
            if opts.o.debug:
                print("PVCs deleted:")
                print(f"{pvc_resp}")
        # Process compose files into a Deployment
        deployment = self.cluster_info.get_deployment()
        # Create the k8s objects
        if opts.o.debug:
            print(f"Deleting this deployment: {deployment}")
        deployment_resp = self.apps_api.delete_namespaced_deployment(
            name=deployment.metadata.name, namespace=self.k8s_namespace
        )
        if self.is_kind():
            # Destroy the kind cluster
            destroy_cluster(self.kind_cluster_name)

    def ps(self):
        self.connect_api()
        # Call whatever API we need to get the running container list
        ret = self.core_api.list_pod_for_all_namespaces(watch=False)
        if ret.items:
            for i in ret.items:
                print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        ret = self.core_api.list_node(pretty=True, watch=False)
        return []

    def port(self, service, private_port):
        # Since we handle the port mapping, need to figure out where this comes from
        # Also look into whether it makes sense to get ports for k8s
        pass

    def execute(self, service_name, command, tty, envs):
        # Call the API to execute a command in a running container
        pass

    def logs(self, services, tail, follow, stream):
        self.connect_api()
        pods = pods_in_deployment(self.core_api, "test-deployment")
        if len(pods) > 1:
            print("Warning: more than one pod in the deployment")
        k8s_pod_name = pods[0]
        log_data = self.core_api.read_namespaced_pod_log(k8s_pod_name, namespace="default", container="test")
        return log_stream_from_string(log_data)

    def run(self, image: str, command=None, user=None, volumes=None, entrypoint=None, env={}, detach=False):
        # We need to figure out how to do this -- check why we're being called first
        pass

    def is_kind(self):
        return self.type == "k8s-kind"


class K8sDeployerConfigGenerator(DeployerConfigGenerator):
    type: str

    def __init__(self, type: str) -> None:
        self.type = type
        super().__init__()

    def generate(self, deployment_dir: Path):
        # No need to do this for the remote k8s case
        if self.type == "k8s-kind":
            # Check the file isn't already there
            # Get the config file contents
            content = generate_kind_config(deployment_dir)
            if opts.o.debug:
                print(f"kind config is: {content}")
            config_file = deployment_dir.joinpath(constants.kind_config_filename)
            # Write the file
            with open(config_file, "w") as output_file:
                output_file.write(content)
