# tests/unit/test_job_image_overrides.py
"""Unit tests for image-overrides applied to k8s Jobs in K8sDeployer._create_jobs()."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _make_job(container_name, image):
    container = SimpleNamespace(name=container_name, image=image)
    return SimpleNamespace(
        metadata=SimpleNamespace(name=f"{container_name}-job", annotations=None),
        spec=SimpleNamespace(
            template=SimpleNamespace(spec=SimpleNamespace(containers=[container]))
        ),
    )


class TestJobImageOverrides(unittest.TestCase):
    def setUp(self):
        from stack_orchestrator.deploy.k8s.deploy_k8s import K8sDeployer

        self.deployer = K8sDeployer.__new__(K8sDeployer)
        self.deployer.k8s_namespace = "test-ns"
        self.deployer.batch_api = MagicMock()
        self.deployer.cluster_info = MagicMock()
        self.deployer.is_kind = MagicMock(return_value=True)

    def _run(self):
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts.o",
            SimpleNamespace(debug=False, dry_run=False),
        ):
            self.deployer._create_jobs()

    def _created_job(self):
        call = self.deployer.batch_api.create_namespaced_job.call_args
        return call.kwargs["body"] if "body" in call.kwargs else call.args[0]

    def test_override_applied_to_job_container(self):
        job = _make_job("deployer", "ghcr.io/x/hyperlane-svm-deployer:latest")
        self.deployer.cluster_info.get_jobs.return_value = [job]
        self.deployer.image_overrides = {
            "deployer": "ghcr.io/x/hyperlane-svm-deployer:v2.2.0-gorbagana.1"
        }
        self._run()
        created = self._created_job()
        self.assertEqual(
            created.spec.template.spec.containers[0].image,
            "ghcr.io/x/hyperlane-svm-deployer:v2.2.0-gorbagana.1",
        )

    def test_unlisted_container_left_untouched(self):
        job = _make_job("deployer", "ghcr.io/x/hyperlane-svm-deployer:latest")
        self.deployer.cluster_info.get_jobs.return_value = [job]
        self.deployer.image_overrides = {"other": "ghcr.io/x/other:v1"}
        self._run()
        created = self._created_job()
        self.assertEqual(
            created.spec.template.spec.containers[0].image,
            "ghcr.io/x/hyperlane-svm-deployer:latest",
        )

    def test_no_overrides_is_noop(self):
        job = _make_job("deployer", "ghcr.io/x/hyperlane-svm-deployer:latest")
        self.deployer.cluster_info.get_jobs.return_value = [job]
        self.deployer.image_overrides = None
        self._run()
        created = self._created_job()
        self.assertEqual(
            created.spec.template.spec.containers[0].image,
            "ghcr.io/x/hyperlane-svm-deployer:latest",
        )


if __name__ == "__main__":
    unittest.main()
