# tests/unit/test_ws_mux.py
"""Unit tests for websocket mux support (spec key, route logic, rendering)."""
import unittest

from stack_orchestrator import constants
from stack_orchestrator.deploy.k8s.ws_mux import validate_http_proxy_routes


def _proxy(host, routes):
    return {"host-name": host, "routes": routes}


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
