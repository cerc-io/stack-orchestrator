# Bug: laconic-so etcd cleanup wipes core kubernetes service

## Summary

`_clean_etcd_keeping_certs()` in laconic-stack-orchestrator 1.1.0 deletes the `kubernetes` service from etcd, breaking cluster networking on restart.

## Component

`stack_orchestrator/deploy/k8s/helpers.py` — `_clean_etcd_keeping_certs()`

## Reproduction

1. Deploy with `laconic-so` to a k8s-kind target with persisted etcd (hostPath mount in kind-config.yml)
2. `laconic-so deployment --dir <dir> stop` (destroys cluster)
3. `laconic-so deployment --dir <dir> start` (recreates cluster with cleaned etcd)

## Symptoms

- `kindnet` pods enter CrashLoopBackOff with: `panic: unable to load in-cluster configuration, KUBERNETES_SERVICE_HOST and KUBERNETES_SERVICE_PORT must be defined`
- `kubectl get svc kubernetes -n default` returns `NotFound`
- coredns, caddy, local-path-provisioner stuck in Pending (no CNI without kindnet)
- No pods can be scheduled

## Root Cause

`_clean_etcd_keeping_certs()` uses a whitelist that only preserves `/registry/secrets/caddy-system` keys. All other etcd keys are deleted, including `/registry/services/specs/default/kubernetes` — the core `kubernetes` ClusterIP service that kube-apiserver auto-creates.

When the kind cluster starts with the cleaned etcd, kube-apiserver sees the existing etcd data and does not re-create the `kubernetes` service. kindnet depends on the `KUBERNETES_SERVICE_HOST` environment variable which is injected by the kubelet from this service — without it, kindnet panics.

## Fix Options

1. **Expand the whitelist** to include `/registry/services/specs/default/kubernetes` and other core cluster resources
2. **Fully wipe etcd** instead of selective cleanup — let the cluster bootstrap fresh (simpler, but loses Caddy TLS certs)
3. **Don't persist etcd at all** — ephemeral etcd means clean state every restart (recommended for kind deployments)

## Workaround

Fully delete the kind cluster before `start`:

```bash
kind delete cluster --name <cluster-name>
laconic-so deployment --dir <dir> start
```

This forces fresh etcd bootstrap. Downside: all other services deployed to the cluster (DaemonSets, other namespaces) are destroyed.

## Impact

- Affects any k8s-kind deployment with persisted etcd
- Cluster is unrecoverable without full destroy+recreate
- All non-laconic-so-managed workloads in the cluster are lost
