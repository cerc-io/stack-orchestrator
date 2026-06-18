# tests/unit/test_user_secrets.py
"""Unit tests for K8sDeployer._create_user_secrets()."""
import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from kubernetes.client.exceptions import ApiException


class TestCreateUserSecrets(unittest.TestCase):
    def setUp(self):
        from stack_orchestrator.deploy.k8s.deploy_k8s import K8sDeployer

        self.deployer = K8sDeployer.__new__(K8sDeployer)
        self.deployer.k8s_namespace = "test-ns"
        self.deployer.core_api = MagicMock()
        self.deployer.cluster_info = MagicMock()

    def _set_spec_secrets(self, secrets):
        self.deployer.cluster_info.spec.get_secrets.return_value = secrets

    def _last_create_body(self):
        call = self.deployer.core_api.create_namespaced_secret.call_args
        if "body" in call.kwargs:
            return call.kwargs["body"]
        return call.args[1]

    def test_env_source_creates_secret(self):
        self._set_spec_secrets({
            "app-secrets": {"keys": {"FOO": {"env": "MY_FOO"}}},
        })
        with patch.dict(os.environ, {"MY_FOO": "bar"}):
            self.deployer._create_user_secrets()
        self.deployer.core_api.create_namespaced_secret.assert_called_once()
        body = self._last_create_body()
        self.assertEqual(body.metadata.name, "app-secrets")
        self.assertEqual(base64.b64decode(body.data["FOO"]).decode(), "bar")

    def test_file_source_creates_secret(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("file-value")
            path = f.name
        try:
            self._set_spec_secrets({
                "app-secrets": {"keys": {"K": {"file": path}}},
            })
            self.deployer._create_user_secrets()
            body = self._last_create_body()
            self.assertEqual(base64.b64decode(body.data["K"]).decode(), "file-value")
        finally:
            Path(path).unlink()

    def test_missing_env_raises(self):
        self._set_spec_secrets({
            "app-secrets": {"keys": {"FOO": {"env": "UNSET_VAR_XYZ"}}},
        })
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(Exception) as ctx:
                self.deployer._create_user_secrets()
            self.assertIn("UNSET_VAR_XYZ", str(ctx.exception))
            self.assertIn("app-secrets", str(ctx.exception))

    def test_missing_file_raises(self):
        self._set_spec_secrets({
            "app-secrets": {"keys": {"K": {"file": "/nonexistent/path/xyz"}}},
        })
        with self.assertRaises(Exception) as ctx:
            self.deployer._create_user_secrets()
        self.assertIn("/nonexistent/path/xyz", str(ctx.exception))

    def test_optional_env_unset_skips_secret(self):
        self._set_spec_secrets({
            "app-secrets": {"keys": {"HOOK": {"env": "UNSET_VAR_XYZ", "optional": True}}},
        })
        with patch.dict(os.environ, {}, clear=True):
            self.deployer._create_user_secrets()
        self.deployer.core_api.create_namespaced_secret.assert_not_called()

    def test_optional_unset_keeps_required_keys(self):
        self._set_spec_secrets({
            "app-secrets": {"keys": {
                "REQUIRED": {"env": "MY_REQUIRED"},
                "HOOK": {"env": "UNSET_VAR_XYZ", "optional": True},
            }},
        })
        with patch.dict(os.environ, {"MY_REQUIRED": "v"}, clear=True):
            self.deployer._create_user_secrets()
        body = self._last_create_body()
        self.assertEqual(base64.b64decode(body.data["REQUIRED"]).decode(), "v")
        self.assertNotIn("HOOK", body.data)

    def test_optional_file_missing_skips_key(self):
        self._set_spec_secrets({
            "app-secrets": {"keys": {
                "REQUIRED": {"env": "MY_REQUIRED"},
                "K": {"file": "/nonexistent/path/xyz", "optional": True},
            }},
        })
        with patch.dict(os.environ, {"MY_REQUIRED": "v"}, clear=True):
            self.deployer._create_user_secrets()
        body = self._last_create_body()
        self.assertNotIn("K", body.data)

    def test_legacy_list_form_skipped(self):
        self._set_spec_secrets({"app-secrets": ["KEY1", "KEY2"]})
        self.deployer._create_user_secrets()
        self.deployer.core_api.create_namespaced_secret.assert_not_called()

    def test_idempotent_409_replaces(self):
        self._set_spec_secrets({
            "app-secrets": {"keys": {"FOO": {"env": "MY_FOO"}}},
        })
        self.deployer.core_api.create_namespaced_secret.side_effect = ApiException(
            status=409, reason="AlreadyExists"
        )
        with patch.dict(os.environ, {"MY_FOO": "bar"}):
            self.deployer._create_user_secrets()
        self.deployer.core_api.replace_namespaced_secret.assert_called_once()


if __name__ == "__main__":
    unittest.main()
