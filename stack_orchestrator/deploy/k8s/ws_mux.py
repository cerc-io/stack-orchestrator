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

"""Websocket mux support for k8s http-proxy.

The k8s Ingress API cannot express header-based routing (same host+path to
one backend for HTTP, another for websocket upgrades). When a spec declares
`websocket: true` routes, SO generates a small Caddy "ws-mux" that performs
the Upgrade split, and points the Ingress at it. This module holds the pure
logic: route validation, mux entry collection, Caddyfile rendering. No
kubernetes imports here — object construction lives in cluster_info.py.
"""

MUX_PORT = 8080


def validate_http_proxy_routes(http_proxy_info_list):
    """Reject route sets the ingress+mux model cannot serve unambiguously.

    Raises ValueError naming the conflicting host/path.
    """
    for proxy in http_proxy_info_list or []:
        host = proxy["host-name"]
        plain_seen = set()
        ws_seen = set()
        for route in proxy.get("routes", []):
            path = route["path"]
            if route.get("websocket"):
                if path in ws_seen:
                    raise ValueError(
                        f"http-proxy: multiple websocket routes for "
                        f"{host}{path}"
                    )
                ws_seen.add(path)
            else:
                if path in plain_seen:
                    raise ValueError(
                        f"http-proxy: duplicate routes for {host}{path} — "
                        f"each host+path may have at most one plain route "
                        f"and one websocket route"
                    )
                plain_seen.add(path)
