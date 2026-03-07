# Bug: laconic-so crashes on re-deploy when caddy ingress already exists

## Summary

`laconic-so deployment start` crashes with `FailToCreateError` when the kind cluster already has caddy ingress resources installed. The deployer uses `create_from_yaml()` which fails on `AlreadyExists` conflicts instead of applying idempotently. This prevents the application deployment from ever being reached — the crash happens before any app manifests are applied.

## Component

`stack_orchestrator/deploy/k8s/deploy_k8s.py:366` — `up()` method
`stack_orchestrator/deploy/k8s/helpers.py:369` — `install_ingress_for_kind()`

## Reproduction

1. `kind delete cluster --name laconic-70ce4c4b47e23b85`
2. `laconic-so deployment --dir /srv/deployments/agave start` — creates cluster, loads images, installs caddy ingress, but times out or is interrupted before app deployment completes
3. `laconic-so deployment --dir /srv/deployments/agave start` — crashes immediately after image loading

## Symptoms

- Traceback ending in:
  ```
  kubernetes.utils.create_from_yaml.FailToCreateError:
    Error from server (Conflict): namespaces "caddy-system" already exists
    Error from server (Conflict): serviceaccounts "caddy-ingress-controller" already exists
    Error from server (Conflict): clusterroles.rbac.authorization.k8s.io "caddy-ingress-controller" already exists
    ...
  ```
- Namespace `laconic-laconic-70ce4c4b47e23b85` exists but is empty — no pods, no deployments, no events
- Cluster is healthy, images are loaded, but no app manifests are applied

## Root Cause

`install_ingress_for_kind()` calls `kubernetes.utils.create_from_yaml()` which uses `POST` (create) semantics. If the resources already exist (from a previous partial run), every resource returns `409 Conflict` and `create_from_yaml` raises `FailToCreateError`, aborting the entire `up()` method before the app deployment step.

The first `laconic-so start` after a fresh `kind delete` works because:
1. Image loading into the kind node takes 5-10 minutes (images are ~10GB+)
2. Caddy ingress is installed successfully
3. App deployment begins

But if that first run is interrupted (timeout, Ctrl-C, ansible timeout), the second run finds caddy already installed and crashes.

## Fix Options

1. **Use server-side apply** instead of `create_from_yaml()` — `kubectl apply` is idempotent
2. **Check if ingress exists before installing** — skip `install_ingress_for_kind()` if caddy-system namespace exists
3. **Catch `AlreadyExists` and continue** — treat 409 as success for infrastructure resources

## Workaround

Delete the caddy ingress resources before re-running:

```bash
kubectl delete namespace caddy-system
kubectl delete clusterrole caddy-ingress-controller
kubectl delete clusterrolebinding caddy-ingress-controller
kubectl delete ingressclass caddy
laconic-so deployment --dir /srv/deployments/agave start
```

Or nuke the entire cluster and start fresh:

```bash
kind delete cluster --name laconic-70ce4c4b47e23b85
laconic-so deployment --dir /srv/deployments/agave start
```

## Interaction with ansible timeout

The `biscayne-redeploy.yml` playbook sets a 600s timeout on the `laconic-so deployment start` task. Image loading alone can exceed this on a fresh cluster (images must be re-loaded into the new kind node). When ansible kills the process at 600s, the caddy ingress is already installed but the app is not — putting the cluster into the broken state described above. Subsequent playbook runs hit this bug on every attempt.

## Impact

- Blocks all re-deploys on biscayne without manual cleanup
- The playbook cannot recover automatically — every retry hits the same conflict
- Discovered 2026-03-05 during full wipe redeploy of biscayne validator
