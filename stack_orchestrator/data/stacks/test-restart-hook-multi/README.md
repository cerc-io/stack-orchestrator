# test-restart-hook-multi

E2E test stack used by `tests/k8s-deploy/run-restart-hook-test.sh` to cover the
multi-repo case: `pods:` references two pod repos, each shipping its own
`deploy/commands.py`. `deploy create` should produce
`<deployment>/hooks/commands_0.py` and `<deployment>/hooks/commands_1.py`, and
`deployment start` should invoke both `start()` hooks (each writes its own
marker file so neither overwrites the other).

The pod repos themselves are created by the test script as bare-repo +
working-clone pairs under `$CERC_REPO_BASE_DIR/test-restart-hook-pod-{a,b}`;
they are not committed to this repository. Each pod repo ships its own
`docker-compose.yml` (resolved by `get_pod_file_path` for dict-form pods) and
`stack/deploy/commands.py` — the stack repo only owns `stack.yml`.
