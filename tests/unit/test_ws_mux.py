# tests/unit/test_ws_mux.py
"""Unit tests for websocket mux support (spec key, route logic, rendering)."""
import unittest

from stack_orchestrator import constants
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
        self.assertIn("header Upgrade websocket", out)
        self.assertIn("reverse_proxy app-svc:8900", out)
        self.assertIn("reverse_proxy app-svc:8899", out)
        # ws backend must appear before the http fallback
        self.assertLess(out.index("app-svc:8900"), out.index("app-svc:8899"))

    def test_ws_only_has_no_header_matcher(self):
        out = render_mux_caddyfile([{
            "host": "a.example.com", "path": "/",
            "ws_backend": "app-svc:8900", "http_backend": None,
        }])
        self.assertNotIn("header Upgrade", out)
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
