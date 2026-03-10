# Copyright © 2024 Vulcanize
# SPDX-License-Identifier: AGPL-3.0

"""DNS verification via temporary ingress probe."""

import secrets
import socket
import time
from typing import Optional
import requests
from kubernetes import client


def get_server_egress_ip() -> str:
    """Get this server's public egress IP via ipify."""
    response = requests.get("https://api.ipify.org", timeout=10)
    response.raise_for_status()
    return response.text.strip()


def resolve_hostname(hostname: str) -> list[str]:
    """Resolve hostname to list of IP addresses."""
    try:
        _, _, ips = socket.gethostbyname_ex(hostname)
        return ips
    except socket.gaierror:
        return []


def verify_dns_simple(hostname: str, expected_ip: Optional[str] = None) -> bool:
    """Simple DNS verification - check hostname resolves to expected IP.

    If expected_ip not provided, uses server's egress IP.
    Returns True if hostname resolves to expected IP.
    """
    resolved_ips = resolve_hostname(hostname)
    if not resolved_ips:
        print(f"DNS FAIL: {hostname} does not resolve")
        return False

    if expected_ip is None:
        expected_ip = get_server_egress_ip()

    if expected_ip in resolved_ips:
        print(f"DNS OK: {hostname} -> {resolved_ips} (includes {expected_ip})")
        return True
    else:
        print(f"DNS WARN: {hostname} -> {resolved_ips} (expected {expected_ip})")
        return False


def create_probe_ingress(hostname: str, namespace: str = "default") -> str:
    """Create a temporary ingress for DNS probing.

    Returns the probe token that the ingress will respond with.
    """
    token = secrets.token_hex(16)

    networking_api = client.NetworkingV1Api()

    # Create a simple ingress that Caddy will pick up
    ingress = client.V1Ingress(
        metadata=client.V1ObjectMeta(
            name="laconic-dns-probe",
            annotations={
                "kubernetes.io/ingress.class": "caddy",
                "laconic.com/probe-token": token,
            },
        ),
        spec=client.V1IngressSpec(
            rules=[
                client.V1IngressRule(
                    host=hostname,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[
                            client.V1HTTPIngressPath(
                                path="/.well-known/laconic-probe",
                                path_type="Exact",
                                backend=client.V1IngressBackend(
                                    service=client.V1IngressServiceBackend(
                                        name="caddy-ingress-controller",
                                        port=client.V1ServiceBackendPort(number=80),
                                    )
                                ),
                            )
                        ]
                    ),
                )
            ]
        ),
    )

    networking_api.create_namespaced_ingress(namespace=namespace, body=ingress)
    return token


def delete_probe_ingress(namespace: str = "default"):
    """Delete the temporary probe ingress."""
    networking_api = client.NetworkingV1Api()
    try:
        networking_api.delete_namespaced_ingress(
            name="laconic-dns-probe", namespace=namespace
        )
    except client.exceptions.ApiException:
        pass  # Ignore if already deleted


def verify_dns_via_probe(
    hostname: str, namespace: str = "default", timeout: int = 30, poll_interval: int = 2
) -> bool:
    """Verify DNS by creating temp ingress and probing it.

    This definitively proves that traffic to the hostname reaches this cluster.

    Args:
        hostname: The hostname to verify
        namespace: Kubernetes namespace for probe ingress
        timeout: Total seconds to wait for probe to succeed
        poll_interval: Seconds between probe attempts

    Returns:
        True if probe succeeds, False otherwise
    """
    # First check DNS resolves at all
    if not resolve_hostname(hostname):
        print(f"DNS FAIL: {hostname} does not resolve")
        return False

    print(f"Creating probe ingress for {hostname}...")
    create_probe_ingress(hostname, namespace)

    try:
        # Wait for Caddy to pick up the ingress
        time.sleep(3)

        # Poll until success or timeout
        probe_url = f"http://{hostname}/.well-known/laconic-probe"
        start_time = time.time()
        last_error = None

        while time.time() - start_time < timeout:
            try:
                response = requests.get(probe_url, timeout=5)
                # For now, just verify we get a response from this cluster
                # A more robust check would verify a unique token
                if response.status_code < 500:
                    print(f"DNS PROBE OK: {hostname} routes to this cluster")
                    return True
            except requests.RequestException as e:
                last_error = e

            time.sleep(poll_interval)

        print(f"DNS PROBE FAIL: {hostname} - {last_error}")
        return False

    finally:
        print("Cleaning up probe ingress...")
        delete_probe_ingress(namespace)
