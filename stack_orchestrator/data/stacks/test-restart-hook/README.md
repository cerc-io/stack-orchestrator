# test-restart-hook

E2E test stack used by `tests/k8s-deploy/run-restart-hook-test.sh`.

The stack ships a single `start()` hook that writes a versioned marker file
into the deployment directory. The test:

1. `deploy create` → asserts `commands.py` was copied into `<deployment>/hooks/`.
2. `deployment start` → asserts the marker file contains the v1 string.
3. Modifies `commands.py` in the stack-source working tree (v1 → v2).
4. `deployment restart` → asserts the new commands.py was re-copied into
   `<deployment>/hooks/` and the marker file now contains the v2 string.

The pod uses a public `busybox` image that just sleeps; the start hook is the
only thing under test.
