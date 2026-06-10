# tests/unit/test_ws_mux.py
"""Unit tests for websocket mux support (spec key, route logic, rendering)."""
import unittest

from stack_orchestrator import constants


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
