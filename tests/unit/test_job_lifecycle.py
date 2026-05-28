# tests/unit/test_job_lifecycle.py
"""Unit tests for the job-suspend + enhanced run-job feature."""
import unittest
from unittest.mock import MagicMock

from stack_orchestrator.command_types import CommandOptions
from stack_orchestrator.deploy.k8s.cluster_info import ClusterInfo, _is_suspended
import stack_orchestrator.opts as _opts_module


def _make_cluster_info(job_yaml_map):
    """Construct a ClusterInfo with the minimum attrs get_jobs() needs."""
    # opts.o must be set before any ClusterInfo method that calls opts.o.debug
    if _opts_module.opts.o is None:
        _opts_module.opts.o = CommandOptions(stack="test-stack")
    ci = ClusterInfo()
    ci.parsed_job_yaml_map = job_yaml_map
    ci.app_name = "test-app"
    ci.stack_name = "test-stack"
    ci.environment_variables = MagicMock()
    ci.environment_variables.map = {}
    ci.spec = MagicMock()
    ci.spec.get_image_registry_config.return_value = None
    ci.spec.get_configmaps.return_value = {}
    ci.spec.get_volumes.return_value = {}
    ci.spec.get_node_affinities.return_value = []
    ci.spec.get_node_tolerations.return_value = []
    ci.spec.get_image_overrides.return_value = {}
    ci.spec.get_kube_security_context.return_value = None
    ci.spec.get_resources.return_value = None
    ci.spec.get_replicas.return_value = 1
    ci.spec.get_privileged.return_value = False
    ci.spec.get_capabilities.return_value = None
    ci.spec.get_host_devices.return_value = []
    ci.spec.get_unlimited_memlock.return_value = False
    ci.spec.get_annotations.return_value = {}
    ci.spec.get_labels.return_value = {}
    ci.spec.get_secrets.return_value = {}
    ci.spec.get_container_resources.return_value = None
    ci.spec.get_container_resources_for.return_value = None
    ci.spec.get_image_registry.return_value = None
    ci.spec.get_http_proxy.return_value = None
    ci.spec.get_volume_resources.return_value = None
    ci.spec.get_volume_resources_for.return_value = None
    ci.spec.is_kind_deployment.return_value = False
    ci.spec.get_runtime_class.return_value = None
    ci.spec.get_maintenance_service.return_value = None
    ci.spec.file_path = None
    return ci


class TestIsSuspended(unittest.TestCase):
    def test_dict_form_true(self):
        svc = {"labels": {"laconic.suspend": "true"}}
        self.assertTrue(_is_suspended(svc))

    def test_dict_form_mixed_case(self):
        svc = {"labels": {"laconic.suspend": "True"}}
        self.assertTrue(_is_suspended(svc))
        svc = {"labels": {"laconic.suspend": "TRUE"}}
        self.assertTrue(_is_suspended(svc))

    def test_dict_form_false(self):
        svc = {"labels": {"laconic.suspend": "false"}}
        self.assertFalse(_is_suspended(svc))

    def test_label_absent(self):
        svc = {"labels": {"other": "x"}}
        self.assertFalse(_is_suspended(svc))

    def test_labels_block_absent(self):
        svc = {"image": "x"}
        self.assertFalse(_is_suspended(svc))

    def test_list_form_true(self):
        svc = {"labels": ["laconic.suspend=true", "other=x"]}
        self.assertTrue(_is_suspended(svc))

    def test_list_form_absent(self):
        svc = {"labels": ["other=x"]}
        self.assertFalse(_is_suspended(svc))

    def test_labels_null(self):
        svc = {"labels": None}
        self.assertFalse(_is_suspended(svc))


class TestGetJobsSuspendLabel(unittest.TestCase):
    def _job_map(self, service_labels=None):
        # Mimics what parse produces for compose-jobs/docker-compose-foo.yml
        service = {"image": "nginx:latest"}
        if service_labels is not None:
            service["labels"] = service_labels
        return {
            "/abs/path/compose-jobs/docker-compose-foo.yml": {
                "services": {"foo": service},
            }
        }

    def test_suspended_label_stamped_when_true(self):
        ci = _make_cluster_info(self._job_map({"laconic.suspend": "true"}))
        jobs = ci.get_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(
            jobs[0].metadata.labels.get("laconic.suspend"), "true"
        )

    def test_suspended_label_absent_when_false(self):
        ci = _make_cluster_info(self._job_map({"laconic.suspend": "false"}))
        jobs = ci.get_jobs()
        self.assertNotIn("laconic.suspend", jobs[0].metadata.labels)

    def test_suspended_label_absent_when_no_labels(self):
        ci = _make_cluster_info(self._job_map(None))
        jobs = ci.get_jobs()
        self.assertNotIn("laconic.suspend", jobs[0].metadata.labels)


class TestGetJobsNameSuffix(unittest.TestCase):
    def _job_map(self):
        return {
            "/abs/path/compose-jobs/docker-compose-foo.yml": {
                "services": {"foo": {"image": "nginx:latest"}},
            }
        }

    def test_default_no_suffix(self):
        ci = _make_cluster_info(self._job_map())
        jobs = ci.get_jobs()
        self.assertEqual(jobs[0].metadata.name, "test-app-job-foo")

    def test_explicit_suffix(self):
        ci = _make_cluster_info(self._job_map())
        jobs = ci.get_jobs(name_suffix="1700000000")
        self.assertEqual(
            jobs[0].metadata.name, "test-app-job-foo-1700000000"
        )

    def test_none_suffix_same_as_default(self):
        ci = _make_cluster_info(self._job_map())
        jobs = ci.get_jobs(name_suffix=None)
        self.assertEqual(jobs[0].metadata.name, "test-app-job-foo")
