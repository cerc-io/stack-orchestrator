# tests/unit/test_job_lifecycle.py
"""Unit tests for the job-suspend + enhanced run-job feature."""
import unittest
from unittest.mock import MagicMock, patch

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


class TestGetJobsExtraEnv(unittest.TestCase):
    def _job_map(self, env=None):
        svc = {"image": "nginx:latest"}
        if env is not None:
            svc["environment"] = env
        return {
            "/abs/path/compose-jobs/docker-compose-foo.yml": {
                "services": {"foo": svc},
            }
        }

    def _env_dict(self, container):
        # V1EnvVar list -> {name: value}
        return {e.name: e.value for e in (container.env or [])}

    def test_extra_env_appended(self):
        ci = _make_cluster_info(self._job_map())
        jobs = ci.get_jobs(extra_env={"FOO": "bar"})
        container = jobs[0].spec.template.spec.containers[0]
        self.assertEqual(self._env_dict(container).get("FOO"), "bar")

    def test_extra_env_overrides_compose_env(self):
        ci = _make_cluster_info(
            self._job_map(env={"FOO": "from-compose"})
        )
        jobs = ci.get_jobs(extra_env={"FOO": "from-extra"})
        container = jobs[0].spec.template.spec.containers[0]
        env = self._env_dict(container)
        # FOO should appear exactly once with the override value.
        names = [e.name for e in container.env]
        self.assertEqual(names.count("FOO"), 1)
        self.assertEqual(env["FOO"], "from-extra")

    def test_no_extra_env_no_change(self):
        ci = _make_cluster_info(self._job_map(env={"FOO": "x"}))
        jobs = ci.get_jobs()
        env = self._env_dict(jobs[0].spec.template.spec.containers[0])
        self.assertEqual(env.get("FOO"), "x")


from kubernetes import client as k8s_client

from stack_orchestrator.deploy.k8s.deploy_k8s import K8sDeployer


def _make_k8s_deployer(jobs):
    d = K8sDeployer.__new__(K8sDeployer)
    d.k8s_namespace = "test-ns"
    d.batch_api = MagicMock()
    d.cluster_info = MagicMock()
    d.cluster_info.get_jobs.return_value = jobs
    d.type = "k8s-kind"
    return d


def _job(name, suspended=False):
    labels = {"app": "x"}
    if suspended:
        labels["laconic.suspend"] = "true"
    return k8s_client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=k8s_client.V1ObjectMeta(name=name, labels=labels),
        spec=k8s_client.V1JobSpec(
            template=k8s_client.V1PodTemplateSpec(),
            backoff_limit=0,
        ),
    )


class TestCreateJobsSkipsSuspended(unittest.TestCase):
    def test_skips_suspended(self):
        jobs = [_job("a"), _job("b", suspended=True), _job("c")]
        d = _make_k8s_deployer(jobs)
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            d._create_jobs()
        names = [
            call.kwargs.get("body").metadata.name
            for call in d.batch_api.create_namespaced_job.call_args_list
        ]
        self.assertEqual(names, ["a", "c"])

    def test_creates_all_when_none_suspended(self):
        jobs = [_job("a"), _job("b")]
        d = _make_k8s_deployer(jobs)
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            d._create_jobs()
        self.assertEqual(d.batch_api.create_namespaced_job.call_count, 2)

    def test_creates_none_when_all_suspended(self):
        jobs = [_job("a", suspended=True), _job("b", suspended=True)]
        d = _make_k8s_deployer(jobs)
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            d._create_jobs()
        d.batch_api.create_namespaced_job.assert_not_called()


class FakeLogResponse:
    """Mimics urllib3 HTTPResponse used by kubernetes client log streaming."""

    def __init__(self, chunks):
        self._chunks = chunks

    def stream(self, amt=None, decode_content=True):
        for c in self._chunks:
            yield c

    def release_conn(self):
        pass


class TestWaitAndStream(unittest.TestCase):
    def _deployer(self):
        d = K8sDeployer.__new__(K8sDeployer)
        d.k8s_namespace = "test-ns"
        d.batch_api = MagicMock()
        d.core_api = MagicMock()
        return d

    def _pod(self, phase, name="pod-1"):
        return k8s_client.V1Pod(
            metadata=k8s_client.V1ObjectMeta(name=name),
            status=k8s_client.V1PodStatus(phase=phase),
        )

    def test_returns_zero_on_success(self):
        d = self._deployer()
        d.core_api.list_namespaced_pod.return_value = (
            k8s_client.V1PodList(items=[self._pod("Running")])
        )
        d.core_api.read_namespaced_pod_log.return_value = FakeLogResponse(
            [b"hello\n", b"world\n"]
        )
        d.batch_api.read_namespaced_job_status.return_value = (
            k8s_client.V1Job(
                status=k8s_client.V1JobStatus(succeeded=1, failed=0)
            )
        )
        rc = d._wait_and_stream(job_name="j-1", timeout_seconds=0)
        self.assertEqual(rc, 0)

    def test_returns_nonzero_on_failure(self):
        d = self._deployer()
        d.core_api.list_namespaced_pod.return_value = (
            k8s_client.V1PodList(items=[self._pod("Running")])
        )
        d.core_api.read_namespaced_pod_log.return_value = FakeLogResponse(
            [b"boom\n"]
        )
        d.batch_api.read_namespaced_job_status.return_value = (
            k8s_client.V1Job(
                status=k8s_client.V1JobStatus(succeeded=0, failed=1)
            )
        )
        rc = d._wait_and_stream(job_name="j-2", timeout_seconds=0)
        self.assertNotEqual(rc, 0)


class TestRunJob(unittest.TestCase):
    def _deployer(self, jobs):
        d = K8sDeployer.__new__(K8sDeployer)
        d.k8s_namespace = "test-ns"
        d.batch_api = MagicMock()
        d.core_api = MagicMock()
        d.deployment_dir = MagicMock()
        # chart_dir must not exist so we take the non-helm path
        chart_dir = MagicMock()
        chart_dir.exists.return_value = False
        d.deployment_dir.__truediv__.return_value = chart_dir
        d.cluster_info = MagicMock()
        d.cluster_info.app_name = "test-app"
        d.cluster_info.get_jobs.return_value = jobs
        d.type = "k8s-kind"
        # connect_api is called by run_job; stub it out.
        d.connect_api = MagicMock()
        d._wait_and_stream = MagicMock(return_value=0)
        return d

    def test_uses_timestamp_suffix(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=True,
                extra_env={},
                timeout_seconds=0,
            )
        kwargs = d.cluster_info.get_jobs.call_args.kwargs
        self.assertEqual(kwargs.get("name_suffix"), "1700000000")

    def test_forwards_extra_env(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=True,
                extra_env={"CHAIN": "gorchain"},
                timeout_seconds=0,
            )
        kwargs = d.cluster_info.get_jobs.call_args.kwargs
        self.assertEqual(kwargs.get("extra_env"), {"CHAIN": "gorchain"})

    def test_warns_for_non_suspended(self):
        not_suspended = _job("test-app-job-warp-deployer", suspended=False)
        d = self._deployer([not_suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock, patch("sys.stderr") as stderr_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "warp-deployer",
                no_wait=True,
                extra_env={},
                timeout_seconds=0,
            )
        written = "".join(
            c.args[0] for c in stderr_mock.write.call_args_list
        )
        self.assertIn("WARNING", written)
        self.assertIn("warp-deployer", written)

    def test_does_not_warn_for_suspended(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock, patch("sys.stderr") as stderr_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=True,
                extra_env={},
                timeout_seconds=0,
            )
        written = "".join(
            c.args[0] for c in stderr_mock.write.call_args_list
        )
        self.assertNotIn("WARNING", written)

    def test_calls_wait_and_stream_unless_no_wait(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=False,
                extra_env={},
                timeout_seconds=0,
            )
        d._wait_and_stream.assert_called_once()

    def test_no_wait_skips_wait_and_stream(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=True,
                extra_env={},
                timeout_seconds=0,
            )
        d._wait_and_stream.assert_not_called()
