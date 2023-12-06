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

from datetime import datetime, timezone

from pathlib import Path
from kubernetes import client, config

from stack_orchestrator import constants
from stack_orchestrator.deploy.deployer import Deployer, DeployerConfigGenerator
from stack_orchestrator.deploy.k8s.helpers import create_cluster, destroy_cluster, load_images_into_kind
from stack_orchestrator.deploy.k8s.helpers import pods_in_deployment, log_stream_from_string, generate_kind_config
from stack_orchestrator.deploy.k8s.cluster_info import ClusterInfo
from stack_orchestrator.opts import opts
from stack_orchestrator.deploy.deployment_context import DeploymentContext
from stack_orchestrator.util import error_exit


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def _check_delete_exception(e: client.exceptions.ApiException):
    if e.status == 404:
        if opts.o.debug:
            print("Failed to delete object, continuing")
    else:
        error_exit(f"k8s api error: {e}")


class K8sDeployer(Deployer):
    name: str = "k8s"
    type: str
    core_api: client.CoreV1Api
    apps_api: client.AppsV1Api
    networking_api: client.NetworkingV1Api
    k8s_namespace: str = "default"
    kind_cluster_name: str
    cluster_info: ClusterInfo
    deployment_dir: Path
    deployment_context: DeploymentContext

    def __init__(self, type, deployment_context: DeploymentContext, compose_files, compose_project_name, compose_env_file) -> None:
        self.type = type
        # TODO: workaround pending refactoring above to cope with being created with a null deployment_context
        if deployment_context is None:
            return
        self.deployment_dir = deployment_context.deployment_dir
        self.deployment_context = deployment_context
        self.kind_cluster_name = compose_project_name
        self.cluster_info = ClusterInfo()
        self.cluster_info.int(compose_files, compose_env_file, compose_project_name, deployment_context.spec)
        if (opts.o.debug):
            print(f"Deployment dir: {deployment_context.deployment_dir}")
            print(f"Compose files: {compose_files}")
            print(f"Project name: {compose_project_name}")
            print(f"Env file: {compose_env_file}")
            print(f"Type: {type}")

    def connect_api(self):
        if self.is_kind():
            config.load_kube_config(context=f"kind-{self.kind_cluster_name}")
        else:
            # Get the config file and pass to load_kube_config()
            config.load_kube_config(config_file=self.deployment_dir.joinpath(constants.kube_config_filename).as_posix())
        self.core_api = client.CoreV1Api()
        self.networking_api = client.NetworkingV1Api()
        self.apps_api = client.AppsV1Api()
        self.custom_obj_api = client.CustomObjectsApi()

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

        service: client.V1Service = self.cluster_info.get_service()
        service_resp = self.core_api.create_namespaced_service(
            namespace=self.k8s_namespace,
            body=service
        )
        if opts.o.debug:
            print("Service created:")
            print(f"{service_resp}")

        # TODO: disable ingress for kind
        ingress: client.V1Ingress = self.cluster_info.get_ingress()

        if opts.o.debug:
            print(f"Sending this ingress: {ingress}")
        ingress_resp = self.networking_api.create_namespaced_ingress(
            namespace=self.k8s_namespace,
            body=ingress
        )
        if opts.o.debug:
            print("Ingress created:")
            print(f"{ingress_resp}")

    def down(self, timeout, volumes):
        self.connect_api()
        # Delete the k8s objects
        # Create the host-path-mounted PVs for this deployment
        pvs = self.cluster_info.get_pvs()
        for pv in pvs:
            if opts.o.debug:
                print(f"Deleting this pv: {pv}")
            try:
                pv_resp = self.core_api.delete_persistent_volume(name=pv.metadata.name)
                if opts.o.debug:
                    print("PV deleted:")
                    print(f"{pv_resp}")
            except client.exceptions.ApiException as e:
                _check_delete_exception(e)

        # Figure out the PVCs for this deployment
        pvcs = self.cluster_info.get_pvcs()
        for pvc in pvcs:
            if opts.o.debug:
                print(f"Deleting this pvc: {pvc}")
            try:
                pvc_resp = self.core_api.delete_namespaced_persistent_volume_claim(
                    name=pvc.metadata.name, namespace=self.k8s_namespace
                )
                if opts.o.debug:
                    print("PVCs deleted:")
                    print(f"{pvc_resp}")
            except client.exceptions.ApiException as e:
                _check_delete_exception(e)
        deployment = self.cluster_info.get_deployment()
        if opts.o.debug:
            print(f"Deleting this deployment: {deployment}")
        try:
            self.apps_api.delete_namespaced_deployment(
                name=deployment.metadata.name, namespace=self.k8s_namespace
            )
        except client.exceptions.ApiException as e:
            _check_delete_exception(e)

        service: client.V1Service = self.cluster_info.get_service()
        if opts.o.debug:
            print(f"Deleting service: {service}")
        try:
            self.core_api.delete_namespaced_service(
                namespace=self.k8s_namespace,
                name=service.metadata.name
            )
        except client.exceptions.ApiException as e:
            _check_delete_exception(e)

        # TODO: disable ingress for kind
        ingress: client.V1Ingress = self.cluster_info.get_ingress()
        if opts.o.debug:
            print(f"Deleting this ingress: {ingress}")
        try:
            self.networking_api.delete_namespaced_ingress(
                name=ingress.metadata.name, namespace=self.k8s_namespace
            )
        except client.exceptions.ApiException as e:
            _check_delete_exception(e)

        if self.is_kind():
            # Destroy the kind cluster
            destroy_cluster(self.kind_cluster_name)

    def status(self):
        self.connect_api()
        # Call whatever API we need to get the running container list
        all_pods = self.core_api.list_pod_for_all_namespaces(watch=False)
        pods = []

        if all_pods.items:
            for p in all_pods.items:
                if self.cluster_info.app_name in p.metadata.name:
                    pods.append(p)

        if not pods:
            return

        hostname = "?"
        ip = "?"
        tls = "?"
        try:
            ingress = self.networking_api.read_namespaced_ingress(namespace=self.k8s_namespace,
                                                                  name=self.cluster_info.get_ingress().metadata.name)

            cert = self.custom_obj_api.get_namespaced_custom_object(
                group="cert-manager.io",
                version="v1",
                namespace=self.k8s_namespace,
                plural="certificates",
                name=ingress.spec.tls[0].secret_name
            )

            hostname = ingress.spec.tls[0].hosts[0]
            ip = ingress.status.load_balancer.ingress[0].ip
            tls = "notBefore: %s, notAfter: %s" % (cert["status"]["notBefore"], cert["status"]["notAfter"])
        except:  # noqa: E722
            pass

        print("Ingress:")
        print("\tHostname:", hostname)
        print("\tIP:", ip)
        print("\tTLS:", tls)
        print("")
        print("Pods:")

        for p in pods:
            if p.metadata.deletion_timestamp:
                print(f"\t{p.metadata.namespace}/{p.metadata.name}: Terminating ({p.metadata.deletion_timestamp})")
            else:
                print(f"\t{p.metadata.namespace}/{p.metadata.name}: Running ({p.metadata.creation_timestamp})")

    def ps(self):
        self.connect_api()
        pods = self.core_api.list_pod_for_all_namespaces(watch=False)

        ret = []

        for p in pods.items:
            if self.cluster_info.app_name in p.metadata.name:
                pod_ip = p.status.pod_ip
                ports = AttrDict()
                for c in p.spec.containers:
                    if c.ports:
                        for prt in c.ports:
                            ports[str(prt.container_port)] = [AttrDict({
                                "HostIp": pod_ip,
                                "HostPort": prt.container_port
                            })]

                ret.append(AttrDict({
                    "id": f"{p.metadata.namespace}/{p.metadata.name}",
                    "name": p.metadata.name,
                    "namespace": p.metadata.namespace,
                    "network_settings": AttrDict({
                        "ports": ports
                    })
                }))

        return ret

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

    def update(self):
        self.connect_api()
        ref_deployment = self.cluster_info.get_deployment()

        deployment = self.apps_api.read_namespaced_deployment(
            name=ref_deployment.metadata.name,
            namespace=self.k8s_namespace
        )

        new_env = ref_deployment.spec.template.spec.containers[0].env
        for container in deployment.spec.template.spec.containers:
            old_env = container.env
            if old_env != new_env:
                container.env = new_env

        deployment.spec.template.metadata.annotations = {
            "kubectl.kubernetes.io/restartedAt": datetime.utcnow()
            .replace(tzinfo=timezone.utc)
            .isoformat()
        }

        self.apps_api.patch_namespaced_deployment(
            name=ref_deployment.metadata.name,
            namespace=self.k8s_namespace,
            body=deployment
        )

    def run(self, image: str, command=None, user=None, volumes=None, entrypoint=None, env={}, ports=[], detach=False):
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
