# Feature: Use local registry for kind image loading

## Summary

`laconic-so deployment start` uses `kind load docker-image` to copy container images from the host Docker daemon into the kind node's containerd. This serializes the full image (`docker save`), pipes it through `docker exec`, and deserializes it (`ctr image import`). For biscayne's ~837MB agave image plus the doublezero image, this takes 5-10 minutes on every cluster recreate — copying between two container runtimes on the same machine.

## Current behavior

```
docker build → host Docker daemon (image stored once)
kind load docker-image → docker save | docker exec kind-node ctr import (full copy)
```

This happens in `stack_orchestrator/deploy/k8s/deploy_k8s.py` every time `laconic-so deployment start` runs and the image isn't already present in the kind node.

## Proposed behavior

Run a persistent local registry (`registry:2`) on the host. `laconic-so` pushes images there after build. Kind's containerd is configured to pull from it.

```
docker build → docker tag localhost:5001/image → docker push localhost:5001/image
kind node containerd → pulls from localhost:5001 (fast, no serialization)
```

The registry container persists across kind cluster deletions. Images are always available without reloading.

## Implementation

1. **Registry container**: `docker run -d --restart=always -p 5001:5000 --name kind-registry registry:2`

2. **Kind config** — add registry mirror to `containerdConfigPatches` in kind-config.yml:
   ```yaml
   containerdConfigPatches:
     - |-
       [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:5001"]
         endpoint = ["http://kind-registry:5000"]
   ```

3. **Connect registry to kind network**: `docker network connect kind kind-registry`

4. **laconic-so change** — in `deploy_k8s.py`, replace `kind load docker-image` with:
   ```python
   # Tag and push to local registry instead of kind load
   docker tag image:local localhost:5001/image:local
   docker push localhost:5001/image:local
   ```

5. **Compose files** — image references change from `laconicnetwork/agave:local` to `localhost:5001/laconicnetwork/agave:local`

Kind documents this pattern: https://kind.sigs.k8s.io/docs/user/local-registry/

## Impact

- Eliminates 5-10 minute image loading step on every cluster recreate
- Registry persists across `kind delete cluster` — no re-push needed unless the image itself changes
- `docker push` to a local registry is near-instant (shared filesystem, layer dedup)
- Unblocks faster iteration on redeploy cycles

## Scope

This is a `stack-orchestrator` change, specifically in `deploy_k8s.py`. The kind-config.yml also needs the registry mirror config, which `laconic-so` generates from `spec.yml`.

## Discovered

2026-03-05 — during biscayne full wipe redeploy, `laconic-so start` spent most of its runtime on `kind load docker-image`, causing ansible timeouts and cascading failures (caddy ingress conflict bug).
