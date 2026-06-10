# tests/unit/test_ws_mux.py
"""Unit tests for websocket mux support (spec key, route logic, rendering)."""
import unittest
from unittest.mock import MagicMock, patch

from kubernetes.client.exceptions import ApiException

from stack_orchestrator import constants
from stack_orchestrator.command_types import CommandOptions
from stack_orchestrator.deploy.k8s.ws_mux import (
    collect_mux_entries,
    render_mux_caddyfile,
    validate_http_proxy_routes,
)


def _proxy(host, routes):
    return {"host-name": host, "routes": routes}


def _resolve(container_name):
    return f"{container_name}-svc"


class TestWsMuxImageKey(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(constants.ws_mux_image_key, "ws-mux-image")
        self.assertEqual(constants.default_ws_mux_image, "caddy:2-alpine")

    def test_spec_accessor_default_and_override(self):
        from stack_orchestrator.deploy.spec import Spec

        spec = Spec(obj={})
        self.assertIsNone(spec.get_ws_mux_image())
        spec = Spec(obj={"ws-mux-image": "caddy:2.8-alpine"})
        self.assertEqual(spec.get_ws_mux_image(), "caddy:2.8-alpine")


class TestValidateHttpProxyRoutes(unittest.TestCase):
    def test_empty_ok(self):
        validate_http_proxy_routes([])

    def test_paired_routes_ok(self):
        validate_http_proxy_routes([_proxy("a.example.com", [
            {"path": "/", "proxy-to": "app:8899"},
            {"path": "/", "proxy-to": "app:8900", "websocket": True},
        ])])

    def test_ws_only_route_ok(self):
        validate_http_proxy_routes([_proxy("a.example.com", [
            {"path": "/", "proxy-to": "app:8900", "websocket": True},
        ])])

    def test_duplicate_plain_routes_error(self):
        with self.assertRaises(ValueError) as ctx:
            validate_http_proxy_routes([_proxy("a.example.com", [
                {"path": "/", "proxy-to": "app:8899"},
                {"path": "/", "proxy-to": "other:9000"},
            ])])
        self.assertIn("a.example.com", str(ctx.exception))
        self.assertIn("/", str(ctx.exception))

    def test_duplicate_ws_routes_error(self):
        with self.assertRaises(ValueError):
            validate_http_proxy_routes([_proxy("a.example.com", [
                {"path": "/", "proxy-to": "app:8900", "websocket": True},
                {"path": "/", "proxy-to": "app:8901", "websocket": True},
            ])])

    def test_same_path_different_hosts_ok(self):
        validate_http_proxy_routes([
            _proxy("a.example.com", [{"path": "/", "proxy-to": "app:8899"}]),
            _proxy("b.example.com", [{"path": "/", "proxy-to": "app:8899"}]),
        ])


class TestCollectMuxEntries(unittest.TestCase):
    def test_no_ws_routes_returns_empty(self):
        entries = collect_mux_entries(
            [_proxy("a.example.com", [{"path": "/", "proxy-to": "app:8899"}])],
            _resolve,
        )
        self.assertEqual(entries, [])

    def test_paired(self):
        entries = collect_mux_entries([_proxy("a.example.com", [
            {"path": "/", "proxy-to": "app:8899"},
            {"path": "/", "proxy-to": "app:8900", "websocket": True},
        ])], _resolve)
        self.assertEqual(entries, [{
            "host": "a.example.com",
            "path": "/",
            "ws_backend": "app-svc:8900",
            "http_backend": "app-svc:8899",
        }])

    def test_ws_only(self):
        entries = collect_mux_entries([_proxy("a.example.com", [
            {"path": "/", "proxy-to": "app:8900", "websocket": True},
        ])], _resolve)
        self.assertEqual(entries[0]["http_backend"], None)


class TestRenderMuxCaddyfile(unittest.TestCase):
    def test_paired_root(self):
        out = render_mux_caddyfile([{
            "host": "a.example.com", "path": "/",
            "ws_backend": "app-svc:8900", "http_backend": "app-svc:8899",
        }])
        self.assertIn("admin off", out)
        self.assertIn("auto_https off", out)
        self.assertIn(":8080 {", out)
        self.assertIn("host a.example.com", out)
        self.assertIn("header_regexp Upgrade (?i)^websocket$", out)
        self.assertIn("reverse_proxy app-svc:8900", out)
        self.assertIn("reverse_proxy app-svc:8899", out)
        # ws backend must appear before the http fallback
        self.assertLess(out.index("app-svc:8900"), out.index("app-svc:8899"))

    def test_ws_only_has_no_header_matcher(self):
        out = render_mux_caddyfile([{
            "host": "a.example.com", "path": "/",
            "ws_backend": "app-svc:8900", "http_backend": None,
        }])
        self.assertNotIn("header_regexp", out)
        self.assertIn("reverse_proxy app-svc:8900", out)

    def test_multi_host_and_subpath_ordering(self):
        out = render_mux_caddyfile([
            {"host": "a.example.com", "path": "/",
             "ws_backend": "a-svc:8900", "http_backend": "a-svc:8899"},
            {"host": "a.example.com", "path": "/sub",
             "ws_backend": "a-svc:9900", "http_backend": "a-svc:9899"},
            {"host": "b.example.com", "path": "/",
             "ws_backend": "b-svc:8900", "http_backend": "b-svc:8899"},
        ])
        self.assertIn("host b.example.com", out)
        # longest path first within a host so /sub isn't shadowed by /
        self.assertLess(out.index("/sub*"), out.index("a-svc:8900"))


def _make_cluster_info(http_proxy):
    from stack_orchestrator.deploy.k8s.cluster_info import ClusterInfo

    ci = ClusterInfo.__new__(ClusterInfo)
    ci.app_name = "testapp"
    ci.stack_name = "test-stack"
    ci.parsed_pod_yaml_map = {"pod1": {"services": {"app": {}}}}
    ci.parsed_job_yaml_map = {}
    ci.spec = MagicMock()
    ci.spec.get_http_proxy.return_value = http_proxy
    ci.spec.get_ws_mux_image.return_value = None
    ci.spec.get_acme_email.return_value = ""
    return ci


PAIRED = [_proxy("a.example.com", [
    {"path": "/", "proxy-to": "app:8899"},
    {"path": "/", "proxy-to": "app:8900", "websocket": True},
])]


class TestGetIngressWithWs(unittest.TestCase):
    def setUp(self):
        self._opts_patch = patch(
            "stack_orchestrator.deploy.k8s.cluster_info.opts.o",
            CommandOptions(stack=""),
        )
        self._opts_patch.start()

    def tearDown(self):
        self._opts_patch.stop()

    def test_paired_routes_emit_single_mux_backend(self):
        ci = _make_cluster_info(PAIRED)
        ingress = ci.get_ingress(use_tls=False)
        paths = ingress.spec.rules[0].http.paths
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].backend.service.name, "testapp-ws-mux")
        self.assertEqual(paths[0].backend.service.port.number, 8080)

    def test_no_ws_routes_unchanged(self):
        ci = _make_cluster_info(
            [_proxy("a.example.com", [{"path": "/", "proxy-to": "app:8899"}])]
        )
        ingress = ci.get_ingress(use_tls=False)
        paths = ingress.spec.rules[0].http.paths
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].backend.service.name, "testapp-service")


class TestGetWsMuxResources(unittest.TestCase):
    def test_none_when_no_ws_routes(self):
        ci = _make_cluster_info(
            [_proxy("a.example.com", [{"path": "/", "proxy-to": "app:8899"}])]
        )
        self.assertIsNone(ci.get_ws_mux_resources())

    def test_objects_generated(self):
        ci = _make_cluster_info(PAIRED)
        res = ci.get_ws_mux_resources()
        cm, dep, svc = res["configmap"], res["deployment"], res["service"]
        self.assertEqual(cm.metadata.name, "testapp-ws-mux-config")
        self.assertIn("reverse_proxy testapp-service:8900", cm.data["Caddyfile"])
        self.assertEqual(dep.metadata.name, "testapp-ws-mux")
        # cleanup sweep finds it via the stack label
        self.assertEqual(
            dep.metadata.labels["app.kubernetes.io/stack"], "test-stack"
        )
        # pod template label is DISTINCT from the main app label so the
        # main app services never select mux pods
        self.assertEqual(
            dep.spec.template.metadata.labels["app"], "testapp-ws-mux"
        )
        self.assertEqual(
            svc.spec.selector["app"], "testapp-ws-mux"
        )
        self.assertEqual(svc.spec.ports[0].port, 8080)
        self.assertEqual(
            dep.spec.template.spec.containers[0].image, "caddy:2-alpine"
        )

    def test_image_override(self):
        ci = _make_cluster_info(PAIRED)
        ci.spec.get_ws_mux_image.return_value = "caddy:2.8-alpine"
        res = ci.get_ws_mux_resources()
        self.assertEqual(
            res["deployment"].spec.template.spec.containers[0].image,
            "caddy:2.8-alpine",
        )


class TestCreateWsMux(unittest.TestCase):
    def setUp(self):
        from stack_orchestrator.deploy.k8s.deploy_k8s import K8sDeployer

        self.deployer = K8sDeployer.__new__(K8sDeployer)
        self.deployer.k8s_namespace = "test-ns"
        self.deployer.core_api = MagicMock()
        self.deployer.apps_api = MagicMock()
        self.deployer.cluster_info = MagicMock()

    def test_noop_when_no_mux(self):
        self.deployer.cluster_info.get_ws_mux_resources.return_value = None
        self.deployer._create_ws_mux()
        self.deployer.core_api.create_namespaced_config_map.assert_not_called()

    def test_creates_all_objects(self):
        cm, dep, svc = MagicMock(), MagicMock(), MagicMock()
        self.deployer.cluster_info.get_ws_mux_resources.return_value = {
            "configmap": cm, "deployment": dep, "service": svc,
        }
        self.deployer._create_ws_mux()
        self.deployer.core_api.create_namespaced_config_map.assert_called_once_with(
            namespace="test-ns", body=cm
        )
        self.deployer.apps_api.create_namespaced_deployment.assert_called_once_with(
            namespace="test-ns", body=dep
        )
        self.deployer.core_api.create_namespaced_service.assert_called_once_with(
            namespace="test-ns", body=svc
        )

    def test_409_replaces(self):
        cm, dep, svc = MagicMock(), MagicMock(), MagicMock()
        self.deployer.cluster_info.get_ws_mux_resources.return_value = {
            "configmap": cm, "deployment": dep, "service": svc,
        }
        conflict = ApiException(status=409)
        self.deployer.core_api.create_namespaced_config_map.side_effect = conflict
        self.deployer.apps_api.create_namespaced_deployment.side_effect = conflict
        self.deployer.core_api.create_namespaced_service.side_effect = conflict
        self.deployer._create_ws_mux()
        self.deployer.core_api.replace_namespaced_config_map.assert_called_once()
        self.deployer.apps_api.replace_namespaced_deployment.assert_called_once()
        self.deployer.core_api.replace_namespaced_service.assert_called_once()
        # replace requires the live object's resource_version; the service
        # additionally needs its cluster_ip carried over (_create_nodeports
        # precedent), so the existing service must be read back first
        self.deployer.core_api.read_namespaced_service.assert_called_once_with(
            name=svc.metadata.name, namespace="test-ns"
        )
        existing_svc = self.deployer.core_api.read_namespaced_service.return_value
        self.assertEqual(
            svc.metadata.resource_version, existing_svc.metadata.resource_version
        )
        self.assertEqual(svc.spec.cluster_ip, existing_svc.spec.cluster_ip)

    def test_non_409_raises(self):
        cm, dep, svc = MagicMock(), MagicMock(), MagicMock()
        self.deployer.cluster_info.get_ws_mux_resources.return_value = {
            "configmap": cm, "deployment": dep, "service": svc,
        }
        self.deployer.core_api.create_namespaced_config_map.side_effect = (
            ApiException(status=500)
        )
        with self.assertRaises(ApiException):
            self.deployer._create_ws_mux()


class TestCreateValidationHook(unittest.TestCase):
    def test_create_operation_rejects_duplicate_routes(self):
        """create_operation must call the route validator before any
        filesystem work. We test the helper it delegates to."""
        from stack_orchestrator.deploy.deployment_create import (
            _check_http_proxy_routes,
        )

        spec = MagicMock()
        spec.get_http_proxy.return_value = [_proxy("a.example.com", [
            {"path": "/", "proxy-to": "app:8899"},
            {"path": "/", "proxy-to": "other:9000"},
        ])]
        with self.assertRaises(SystemExit):
            _check_http_proxy_routes(spec)

    def test_valid_routes_pass(self):
        from stack_orchestrator.deploy.deployment_create import (
            _check_http_proxy_routes,
        )

        spec = MagicMock()
        spec.get_http_proxy.return_value = [_proxy("a.example.com", [
            {"path": "/", "proxy-to": "app:8899"},
            {"path": "/", "proxy-to": "app:8900", "websocket": True},
        ])]
        _check_http_proxy_routes(spec)


class TestIngressSslRedirectAnnotation(unittest.TestCase):
    def setUp(self):
        from stack_orchestrator.command_types import CommandOptions
        from stack_orchestrator.opts import opts as so_opts

        self._saved_o = so_opts.o
        so_opts.o = CommandOptions(stack="")

    def tearDown(self):
        from stack_orchestrator.opts import opts as so_opts

        so_opts.o = self._saved_o

    def test_no_tls_disables_ssl_redirect(self):
        ci = _make_cluster_info(
            [_proxy("a.example.com", [{"path": "/", "proxy-to": "app:8899"}])]
        )
        ingress = ci.get_ingress(use_tls=False)
        self.assertEqual(
            ingress.metadata.annotations[
                "caddy.ingress.kubernetes.io/disable-ssl-redirect"
            ],
            "true",
        )

    def test_no_tls_with_acme_email_keeps_ssl_redirect(self):
        # kind cluster serving real TLS via Caddy ACME (acme-email set):
        # the redirect is load-bearing and must survive
        ci = _make_cluster_info(
            [_proxy("a.example.com", [{"path": "/", "proxy-to": "app:8899"}])]
        )
        ci.spec.get_acme_email.return_value = "admin@example.com"
        ingress = ci.get_ingress(use_tls=False)
        self.assertNotIn(
            "caddy.ingress.kubernetes.io/disable-ssl-redirect",
            ingress.metadata.annotations,
        )

    def test_tls_keeps_ssl_redirect(self):
        ci = _make_cluster_info(
            [_proxy("a.example.com", [{"path": "/", "proxy-to": "app:8899"}])]
        )
        ingress = ci.get_ingress(use_tls=True)
        self.assertNotIn(
            "caddy.ingress.kubernetes.io/disable-ssl-redirect",
            ingress.metadata.annotations,
        )


class TestMuxRolloutAnnotation(unittest.TestCase):
    def test_pod_template_carries_caddyfile_hash(self):
        ci = _make_cluster_info(PAIRED)
        res = ci.get_ws_mux_resources()
        annotations = res["deployment"].spec.template.metadata.annotations
        digest = annotations["stack-orchestrator/caddyfile-sha256"]
        import hashlib

        expected = hashlib.sha256(
            res["configmap"].data["Caddyfile"].encode()
        ).hexdigest()
        self.assertEqual(digest, expected)
