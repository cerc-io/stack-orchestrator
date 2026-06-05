"""Unit tests for K8sDeployer._create_jobs() recreate behavior."""
import unittest
from unittest.mock import MagicMock, patch

from kubernetes.client.exceptions import ApiException

from stack_orchestrator.command_types import CommandOptions


class TestCreateJobsRecreate(unittest.TestCase):
    def setUp(self):
        from stack_orchestrator.deploy.k8s.deploy_k8s import K8sDeployer

        self.deployer = K8sDeployer.__new__(K8sDeployer)
        self.deployer.type = "k8s"
        self.deployer.k8s_namespace = "test-ns"
        self.deployer.batch_api = MagicMock()
        self.deployer.cluster_info = MagicMock()
        self._opts_patch = patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts.o",
            CommandOptions(stack=""),
        )
        self._opts_patch.start()

    def tearDown(self):
        self._opts_patch.stop()

    def test_recreate_deletes_then_creates(self):
        job = MagicMock()
        job.metadata.name = "warp-deployer-job"
        job.metadata.annotations = {"laconic.recreate-job": "true"}
        self.deployer.cluster_info.get_jobs = lambda image_pull_policy=None: [job]
        # read returns 404 immediately after delete -> _delete_job_and_wait returns
        self.deployer.batch_api.read_namespaced_job.side_effect = ApiException(
            status=404
        )
        self.deployer._create_jobs()
        self.deployer.batch_api.delete_namespaced_job.assert_called_once()
        self.deployer.batch_api.create_namespaced_job.assert_called_once()

    def test_no_annotation_skips_delete(self):
        job = MagicMock()
        job.metadata.name = "warp-deployer-job"
        job.metadata.annotations = None
        self.deployer.cluster_info.get_jobs = lambda image_pull_policy=None: [job]
        self.deployer._create_jobs()
        self.deployer.batch_api.delete_namespaced_job.assert_not_called()
        self.deployer.batch_api.create_namespaced_job.assert_called_once()


class TestGetJobsRecreateAnnotation(unittest.TestCase):
    """Exercise the label->annotation logic in ClusterInfo.get_jobs()."""

    def _build_jobs(self, services):
        from stack_orchestrator.deploy.k8s.cluster_info import ClusterInfo

        ci = ClusterInfo.__new__(ClusterInfo)
        ci.app_name = "myapp"
        ci.spec = MagicMock()
        ci.spec.get_image_registry_config.return_value = None
        ci.parsed_job_yaml_map = {"docker-compose-foo.yml": {}}
        ci._stack_labels = lambda extra=None: {"app": ci.app_name}
        ci._build_containers = MagicMock(return_value=([], [], services, []))
        return ci.get_jobs()

    def test_dict_label_true_sets_annotation(self):
        jobs = self._build_jobs({"svc": {"labels": {"laconic.recreate-job": "true"}}})
        self.assertEqual(jobs[0].metadata.annotations, {"laconic.recreate-job": "true"})

    def test_list_label_true_sets_annotation(self):
        jobs = self._build_jobs({"svc": {"labels": ["laconic.recreate-job=true"]}})
        self.assertEqual(jobs[0].metadata.annotations, {"laconic.recreate-job": "true"})

    def test_no_label_leaves_annotation_none(self):
        jobs = self._build_jobs({"svc": {"labels": {}}})
        self.assertIsNone(jobs[0].metadata.annotations)


if __name__ == "__main__":
    unittest.main()
