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


def collect_mux_entries(http_proxy_info_list, resolve_service):
    """Collect websocket mux entries: one per (host, path) with a ws route.

    resolve_service: callable(container_name) -> k8s service name.
    Returns a list of dicts:
      {host, path, ws_backend: "svc:port", http_backend: "svc:port" | None}
    """
    entries = []
    for proxy in http_proxy_info_list or []:
        host = proxy["host-name"]
        plain = {}
        ws = {}
        for route in proxy.get("routes", []):
            container, port = route["proxy-to"].split(":")
            backend = f"{resolve_service(container)}:{int(port)}"
            if route.get("websocket"):
                ws[route["path"]] = backend
            else:
                plain[route["path"]] = backend
        for path, ws_backend in ws.items():
            entries.append({
                "host": host,
                "path": path,
                "ws_backend": ws_backend,
                "http_backend": plain.get(path),
            })
    return entries


def _path_matcher(path):
    # Prefix semantics to match Ingress path_type=Prefix
    return None if path == "/" else f"{path.rstrip('/')}*"


def render_mux_caddyfile(entries):
    """Render the ws-mux Caddyfile for the given entries.

    One handle block per host; within it, longest path first so subpaths
    are not shadowed; per path, an Upgrade-header matcher routes to the ws
    backend with fallthrough to the paired HTTP backend (or a direct proxy
    when there is no pair).
    """
    lines = [
        "{",
        "\tadmin off",
        "\tauto_https off",
        "}",
        "",
        f":{MUX_PORT} {{",
    ]
    hosts = sorted({e["host"] for e in entries})
    for h_idx, host in enumerate(hosts):
        host_entries = sorted(
            (e for e in entries if e["host"] == host),
            key=lambda e: len(e["path"]),
            reverse=True,
        )
        lines.append(f"\t@host{h_idx} host {host}")
        lines.append(f"\thandle @host{h_idx} {{")
        for p_idx, entry in enumerate(host_entries):
            matcher = _path_matcher(entry["path"])
            indent = "\t\t"
            if matcher:
                lines.append(f"{indent}handle {matcher} {{")
                indent += "\t"
            if entry["http_backend"]:
                ws_name = f"@ws{h_idx}_{p_idx}"
                lines.append(f"{indent}{ws_name} {{")
                lines.append(f"{indent}\theader Connection *Upgrade*")
                lines.append(f"{indent}\theader Upgrade websocket")
                lines.append(f"{indent}}}")
                lines.append(f"{indent}handle {ws_name} {{")
                lines.append(
                    f"{indent}\treverse_proxy {entry['ws_backend']}"
                )
                lines.append(f"{indent}}}")
                lines.append(f"{indent}handle {{")
                lines.append(
                    f"{indent}\treverse_proxy {entry['http_backend']}"
                )
                lines.append(f"{indent}}}")
            else:
                lines.append(
                    f"{indent}reverse_proxy {entry['ws_backend']}"
                )
            if matcher:
                lines.append("\t\t}")
        lines.append("\t}")
    lines.append("}")
    return "\n".join(lines) + "\n"
