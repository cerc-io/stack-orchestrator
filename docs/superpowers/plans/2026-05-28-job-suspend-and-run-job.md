# Job Suspension and Enhanced `run-job` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compose-level `laconic.suspend` label so individual jobs are skipped at `deployment start`, and extend the existing `run-job` subcommand with timestamp-suffixed Job names, `--env KEY=VAL`, blocking log-stream by default, and `--no-wait`/`--timeout` opt-outs.

**Architecture:** Single builder path — `cluster_info.get_jobs()` grows two kwargs (`extra_env`, `name_suffix`) and stamps a `laconic.suspend` label onto each `V1Job` from the source compose service. `_create_jobs()` filters by that label; `run_job()` finds Jobs by base name, generates a fresh timestamp-suffixed Job per invocation, applies per-invocation env vars, and (unless `--no-wait`) blocks while streaming the pod's logs.

**Tech Stack:** Python 3, kubernetes-client (`batch_api`, `core_api`, `watch.Watch`), click, pytest/unittest.

**Spec:** `docs/superpowers/specs/2026-05-28-job-suspend-and-run-job-design.md` (commit `82a21159`).

---

## File Structure

**Modified:**
- `stack_orchestrator/deploy/k8s/cluster_info.py` — `_is_suspended()` module-level helper; `get_jobs()` accepts `extra_env: Dict[str,str] = None`, `name_suffix: Optional[str] = None`, and stamps `laconic.suspend` on each Job's labels.
- `stack_orchestrator/deploy/k8s/deploy_k8s.py` — `_create_jobs()` filters suspended Jobs by label; `_wait_and_stream()` helper added; `run_job()` adds timestamp suffix, forwards `extra_env`, calls `_wait_and_stream()` unless `no_wait`, prints warning for non-suspended.
- `stack_orchestrator/deploy/deployer.py` — abstract `run_job` signature grows three kwargs (`extra_env`, `no_wait`, `timeout_seconds`).
- `stack_orchestrator/deploy/compose/deploy_docker.py` — `run_job` accepts the new kwargs; warns + ignores `extra_env`; raises for non-default `no_wait` / `timeout_seconds`.
- `stack_orchestrator/deploy/deploy.py` — `run_job_operation()` parses/validates `--env KEY=VAL` and forwards the kwargs.
- `stack_orchestrator/deploy/deployment.py` — Click decorator for `run_job` gains `--env`, `--no-wait`, `--timeout`.
- `docs/cli.md` — documents the new flags and the label.

**Added:**
- `tests/unit/test_job_lifecycle.py` — all unit tests for the feature live here.

No file deletions.

---

## Conventions

- Tests live under `tests/unit/` per existing layout (see `tests/unit/test_user_secrets.py`). Use `unittest.TestCase` + `unittest.mock`; pytest collects them.
- Construct `K8sDeployer` via `K8sDeployer.__new__(K8sDeployer)` and set only the attributes needed (matches the existing `test_user_secrets.py` style).
- Construct `ClusterInfo` directly via `ClusterInfo()` and set attributes (`parsed_job_yaml_map`, `app_name`, `spec`, etc.) manually since `int()` is the production initializer and not test-friendly.
- Run a single unit test with `pytest tests/unit/test_job_lifecycle.py::ClassName::test_name -v`.
- Run the full new unit module with `pytest tests/unit/test_job_lifecycle.py -v`.
- Commit messages follow conventional style: `feat: …`, `test: …`, `docs: …`. No branch names in commit messages.

---

## Task 1: `_is_suspended` helper

**Files:**
- Modify: `stack_orchestrator/deploy/k8s/cluster_info.py` (top-level, near other module-level helpers)
- Test: `tests/unit/test_job_lifecycle.py` (create)

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_job_lifecycle.py`:

```python
# tests/unit/test_job_lifecycle.py
"""Unit tests for the job-suspend + enhanced run-job feature."""
import unittest

from stack_orchestrator.deploy.k8s.cluster_info import _is_suspended


class TestIsSuspended(unittest.TestCase):
    def test_dict_form_true(self):
        svc = {"labels": {"laconic.suspend": "true"}}
        self.assertTrue(_is_suspended(svc))

    def test_dict_form_mixed_case(self):
        svc = {"labels": {"laconic.suspend": "True"}}
        self.assertTrue(_is_suspended(svc))
        svc = {"labels": {"laconic.suspend": "TRUE"}}
        self.assertTrue(_is_suspended(svc))

    def test_dict_form_false(self):
        svc = {"labels": {"laconic.suspend": "false"}}
        self.assertFalse(_is_suspended(svc))

    def test_label_absent(self):
        svc = {"labels": {"other": "x"}}
        self.assertFalse(_is_suspended(svc))

    def test_labels_block_absent(self):
        svc = {"image": "x"}
        self.assertFalse(_is_suspended(svc))

    def test_list_form_true(self):
        svc = {"labels": ["laconic.suspend=true", "other=x"]}
        self.assertTrue(_is_suspended(svc))

    def test_list_form_absent(self):
        svc = {"labels": ["other=x"]}
        self.assertFalse(_is_suspended(svc))

    def test_labels_null(self):
        svc = {"labels": None}
        self.assertFalse(_is_suspended(svc))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestIsSuspended -v`
Expected: FAIL with `ImportError: cannot import name '_is_suspended'`.

- [ ] **Step 3: Add the helper**

Append to `stack_orchestrator/deploy/k8s/cluster_info.py` (place near other top-level helpers, e.g. just above `class ClusterInfo:`):

```python
def _is_suspended(service: dict) -> bool:
    """Return True if the compose service has label laconic.suspend == 'true'."""
    labels = service.get("labels") or {}
    if isinstance(labels, list):
        parsed = {}
        for item in labels:
            if not isinstance(item, str):
                continue
            key, _, value = item.partition("=")
            parsed[key] = value
        labels = parsed
    return str(labels.get("laconic.suspend", "")).lower() == "true"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestIsSuspended -v`
Expected: PASS — 8 tests.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/k8s/cluster_info.py tests/unit/test_job_lifecycle.py
git commit -m "feat: _is_suspended helper for compose laconic.suspend label"
```

---

## Task 2: `get_jobs()` stamps `laconic.suspend` label

The Job builder must propagate the source service's suspend state into the V1Job's metadata.labels so downstream code (`_create_jobs()`, `run_job()`) can read it without re-parsing the compose YAML.

**Files:**
- Modify: `stack_orchestrator/deploy/k8s/cluster_info.py:1106-1174` (the `get_jobs` method)
- Test: `tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_job_lifecycle.py`:

```python
from unittest.mock import MagicMock, patch

from stack_orchestrator.deploy.k8s.cluster_info import ClusterInfo


def _make_cluster_info(job_yaml_map):
    """Construct a ClusterInfo with the minimum attrs get_jobs() needs."""
    ci = ClusterInfo()
    ci.parsed_job_yaml_map = job_yaml_map
    ci.app_name = "test-app"
    ci.stack_name = "test-stack"
    ci.environment_variables = MagicMock()
    ci.environment_variables.map = {}
    ci.spec = MagicMock()
    ci.spec.get_image_registry_config.return_value = None
    ci.spec.get_configmaps.return_value = {}
    ci.spec.get_volumes.return_value = {}
    ci.spec.get_node_affinities.return_value = []
    ci.spec.get_node_tolerations.return_value = []
    ci.spec.get_image_overrides.return_value = {}
    ci.spec.get_kube_security_context.return_value = None
    ci.spec.get_resources.return_value = None
    ci.spec.get_replicas.return_value = 1
    ci.spec.get_privileged.return_value = False
    ci.spec.get_capabilities.return_value = None
    ci.spec.get_host_devices.return_value = []
    ci.spec.get_unlimited_memlock.return_value = False
    ci.spec.get_annotations.return_value = {}
    ci.spec.get_labels.return_value = {}
    ci.spec.get_secrets.return_value = {}
    return ci


class TestGetJobsSuspendLabel(unittest.TestCase):
    def _job_map(self, service_labels=None):
        # Mimics what parse produces for compose-jobs/docker-compose-foo.yml
        service = {"image": "nginx:latest"}
        if service_labels is not None:
            service["labels"] = service_labels
        return {
            "/abs/path/compose-jobs/docker-compose-foo.yml": {
                "services": {"foo": service},
            }
        }

    def test_suspended_label_stamped_when_true(self):
        ci = _make_cluster_info(self._job_map({"laconic.suspend": "true"}))
        jobs = ci.get_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(
            jobs[0].metadata.labels.get("laconic.suspend"), "true"
        )

    def test_suspended_label_absent_when_false(self):
        ci = _make_cluster_info(self._job_map({"laconic.suspend": "false"}))
        jobs = ci.get_jobs()
        self.assertNotIn("laconic.suspend", jobs[0].metadata.labels)

    def test_suspended_label_absent_when_no_labels(self):
        ci = _make_cluster_info(self._job_map(None))
        jobs = ci.get_jobs()
        self.assertNotIn("laconic.suspend", jobs[0].metadata.labels)
```

> **Note for implementer:** The `_make_cluster_info()` helper returns enough MagicMocks for `_build_containers()` to run without crashing. If `_build_containers()` requires additional spec methods, mock them too with reasonable returns (look at the method body in `cluster_info.py` to add what's missing).

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestGetJobsSuspendLabel -v`
Expected: FAIL — current `get_jobs()` does not add `laconic.suspend` to the Job's labels.

- [ ] **Step 3: Modify `get_jobs()`**

In `stack_orchestrator/deploy/k8s/cluster_info.py`, replace the body of the `for job_file in self.parsed_job_yaml_map:` loop in `get_jobs()` so the `job_labels` dict is enriched with `laconic.suspend`:

```python
        for job_file in self.parsed_job_yaml_map:
            # Build containers for this single job file
            single_job_map = {job_file: self.parsed_job_yaml_map[job_file]}
            containers, init_containers, _services, volumes = self._build_containers(
                single_job_map, image_pull_policy
            )

            # Derive job name from file path: docker-compose-<name>.yml -> <name>
            base = os.path.basename(job_file)
            job_name = base
            if job_name.startswith("docker-compose-"):
                job_name = job_name[len("docker-compose-") :]
            if job_name.endswith(".yml"):
                job_name = job_name[: -len(".yml")]
            elif job_name.endswith(".yaml"):
                job_name = job_name[: -len(".yaml")]

            # Detect suspend label on the compose service for this job file.
            services = (
                self.parsed_job_yaml_map[job_file].get("services") or {}
            )
            suspended = any(_is_suspended(svc) for svc in services.values())

            pod_labels = self._stack_labels({"app": f"{self.app_name}-job"})
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=pod_labels),
                spec=client.V1PodSpec(
                    containers=containers,
                    init_containers=init_containers or None,
                    image_pull_secrets=image_pull_secrets,
                    volumes=volumes,
                    restart_policy="Never",
                ),
            )
            job_spec = client.V1JobSpec(
                template=template,
                backoff_limit=0,
            )
            job_labels = self._stack_labels()
            if suspended:
                job_labels["laconic.suspend"] = "true"
            job = client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=client.V1ObjectMeta(
                    name=f"{self.app_name}-job-{job_name}",
                    labels=job_labels,
                ),
                spec=job_spec,
            )
            jobs.append(job)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestGetJobsSuspendLabel -v`
Expected: PASS — 3 tests.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/k8s/cluster_info.py tests/unit/test_job_lifecycle.py
git commit -m "feat: stamp laconic.suspend label on built V1Job when present in compose"
```

---

## Task 3: `get_jobs()` accepts `name_suffix` kwarg

**Files:**
- Modify: `stack_orchestrator/deploy/k8s/cluster_info.py` (`get_jobs` signature + name construction)
- Test: `tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_job_lifecycle.py`:

```python
class TestGetJobsNameSuffix(unittest.TestCase):
    def _job_map(self):
        return {
            "/abs/path/compose-jobs/docker-compose-foo.yml": {
                "services": {"foo": {"image": "nginx:latest"}},
            }
        }

    def test_default_no_suffix(self):
        ci = _make_cluster_info(self._job_map())
        jobs = ci.get_jobs()
        self.assertEqual(jobs[0].metadata.name, "test-app-job-foo")

    def test_explicit_suffix(self):
        ci = _make_cluster_info(self._job_map())
        jobs = ci.get_jobs(name_suffix="1700000000")
        self.assertEqual(
            jobs[0].metadata.name, "test-app-job-foo-1700000000"
        )

    def test_none_suffix_same_as_default(self):
        ci = _make_cluster_info(self._job_map())
        jobs = ci.get_jobs(name_suffix=None)
        self.assertEqual(jobs[0].metadata.name, "test-app-job-foo")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestGetJobsNameSuffix -v`
Expected: FAIL on `test_explicit_suffix` with `TypeError: get_jobs() got an unexpected keyword argument 'name_suffix'`.

- [ ] **Step 3: Modify `get_jobs()` signature and name construction**

In `cluster_info.py`, change:

```python
    def get_jobs(self, image_pull_policy: Optional[str] = None) -> List[client.V1Job]:
```

to:

```python
    def get_jobs(
        self,
        image_pull_policy: Optional[str] = None,
        name_suffix: Optional[str] = None,
    ) -> List[client.V1Job]:
```

In the same method, change the metadata `name=` line:

```python
                metadata=client.V1ObjectMeta(
                    name=f"{self.app_name}-job-{job_name}",
                    labels=job_labels,
                ),
```

to:

```python
                full_name = f"{self.app_name}-job-{job_name}"
                if name_suffix:
                    full_name = f"{full_name}-{name_suffix}"
                metadata = client.V1ObjectMeta(
                    name=full_name,
                    labels=job_labels,
                )
```

Then replace the V1Job creation to use that metadata:

```python
            job = client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=metadata,
                spec=job_spec,
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestGetJobsNameSuffix -v`
Expected: PASS — 3 tests.

Also re-run the prior tests to make sure they still pass:

Run: `pytest tests/unit/test_job_lifecycle.py -v`
Expected: all previously-passing tests still PASS.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/k8s/cluster_info.py tests/unit/test_job_lifecycle.py
git commit -m "feat: get_jobs accepts name_suffix for repeatable Job creation"
```

---

## Task 4: `get_jobs()` accepts `extra_env` kwarg

**Files:**
- Modify: `stack_orchestrator/deploy/k8s/cluster_info.py` (signature + container env merge)
- Test: `tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_job_lifecycle.py`:

```python
class TestGetJobsExtraEnv(unittest.TestCase):
    def _job_map(self, env=None):
        svc = {"image": "nginx:latest"}
        if env is not None:
            svc["environment"] = env
        return {
            "/abs/path/compose-jobs/docker-compose-foo.yml": {
                "services": {"foo": svc},
            }
        }

    def _env_dict(self, container):
        # V1EnvVar list -> {name: value}
        return {e.name: e.value for e in (container.env or [])}

    def test_extra_env_appended(self):
        ci = _make_cluster_info(self._job_map())
        jobs = ci.get_jobs(extra_env={"FOO": "bar"})
        container = jobs[0].spec.template.spec.containers[0]
        self.assertEqual(self._env_dict(container).get("FOO"), "bar")

    def test_extra_env_overrides_compose_env(self):
        ci = _make_cluster_info(
            self._job_map(env={"FOO": "from-compose"})
        )
        jobs = ci.get_jobs(extra_env={"FOO": "from-extra"})
        container = jobs[0].spec.template.spec.containers[0]
        env = self._env_dict(container)
        # FOO should appear exactly once with the override value.
        names = [e.name for e in container.env]
        self.assertEqual(names.count("FOO"), 1)
        self.assertEqual(env["FOO"], "from-extra")

    def test_no_extra_env_no_change(self):
        ci = _make_cluster_info(self._job_map(env={"FOO": "x"}))
        jobs = ci.get_jobs()
        env = self._env_dict(jobs[0].spec.template.spec.containers[0])
        self.assertEqual(env.get("FOO"), "x")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestGetJobsExtraEnv -v`
Expected: FAIL with `TypeError: get_jobs() got an unexpected keyword argument 'extra_env'`.

- [ ] **Step 3: Modify `get_jobs()` to merge `extra_env`**

In `cluster_info.py`, extend the signature:

```python
    def get_jobs(
        self,
        image_pull_policy: Optional[str] = None,
        name_suffix: Optional[str] = None,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> List[client.V1Job]:
```

After the line `containers, init_containers, _services, volumes = self._build_containers(...)` inside the loop, add the env-merge logic:

```python
            if extra_env:
                for container in containers:
                    existing = list(container.env or [])
                    # Keep all existing entries whose name is NOT being overridden.
                    keep = [
                        e for e in existing if e.name not in extra_env
                    ]
                    overrides = [
                        client.V1EnvVar(name=k, value=str(v))
                        for k, v in extra_env.items()
                    ]
                    container.env = keep + overrides
```

> **Implementation note:** `client.V1EnvVar` is already imported in this module (used elsewhere). If it isn't in scope at the call site, the alias is `client.V1EnvVar` via the existing `from kubernetes import client` import.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestGetJobsExtraEnv -v`
Expected: PASS — 3 tests.

Re-run the whole file:

Run: `pytest tests/unit/test_job_lifecycle.py -v`
Expected: all previous tests still PASS.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/k8s/cluster_info.py tests/unit/test_job_lifecycle.py
git commit -m "feat: get_jobs accepts extra_env to layer per-invocation vars"
```

---

## Task 5: `_create_jobs()` skips suspended jobs

**Files:**
- Modify: `stack_orchestrator/deploy/k8s/deploy_k8s.py:847-875` (`_create_jobs`)
- Test: `tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_job_lifecycle.py`:

```python
from kubernetes import client as k8s_client

from stack_orchestrator.deploy.k8s.deploy_k8s import K8sDeployer


def _make_k8s_deployer(jobs):
    d = K8sDeployer.__new__(K8sDeployer)
    d.k8s_namespace = "test-ns"
    d.batch_api = MagicMock()
    d.cluster_info = MagicMock()
    d.cluster_info.get_jobs.return_value = jobs
    d.type = "k8s-kind"
    return d


def _job(name, suspended=False):
    labels = {"app": "x"}
    if suspended:
        labels["laconic.suspend"] = "true"
    return k8s_client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=k8s_client.V1ObjectMeta(name=name, labels=labels),
        spec=k8s_client.V1JobSpec(
            template=k8s_client.V1PodTemplateSpec(),
            backoff_limit=0,
        ),
    )


class TestCreateJobsSkipsSuspended(unittest.TestCase):
    def test_skips_suspended(self):
        jobs = [_job("a"), _job("b", suspended=True), _job("c")]
        d = _make_k8s_deployer(jobs)
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            d._create_jobs()
        names = [
            call.kwargs.get("body").metadata.name
            for call in d.batch_api.create_namespaced_job.call_args_list
        ]
        self.assertEqual(names, ["a", "c"])

    def test_creates_all_when_none_suspended(self):
        jobs = [_job("a"), _job("b")]
        d = _make_k8s_deployer(jobs)
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            d._create_jobs()
        self.assertEqual(d.batch_api.create_namespaced_job.call_count, 2)

    def test_creates_none_when_all_suspended(self):
        jobs = [_job("a", suspended=True), _job("b", suspended=True)]
        d = _make_k8s_deployer(jobs)
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            d._create_jobs()
        d.batch_api.create_namespaced_job.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestCreateJobsSkipsSuspended -v`
Expected: FAIL — current `_create_jobs()` creates all jobs.

- [ ] **Step 3: Filter suspended Jobs in `_create_jobs()`**

In `stack_orchestrator/deploy/k8s/deploy_k8s.py`, replace `_create_jobs()`:

```python
    def _create_jobs(self):
        # Process job compose files into k8s Jobs.
        # Jobs whose source compose service has label laconic.suspend=true
        # are skipped here; they're triggered on demand via `run-job`.
        job_pull_policy = "IfNotPresent" if self.is_kind() else "Always"
        jobs = self.cluster_info.get_jobs(image_pull_policy=job_pull_policy)
        for job in jobs:
            labels = (job.metadata.labels or {}) if job.metadata else {}
            if labels.get("laconic.suspend") == "true":
                if opts.o.debug:
                    print(
                        f"Skipping suspended job {job.metadata.name} "
                        f"(triggered manually via run-job)"
                    )
                continue
            if opts.o.debug:
                print(f"Sending this job: {job}")
            if not opts.o.dry_run:
                job_name = job.metadata.name
                try:
                    job_resp = self.batch_api.create_namespaced_job(
                        body=job, namespace=self.k8s_namespace
                    )
                    if opts.o.debug:
                        print("Job created:")
                        if job_resp.metadata:
                            print(
                                f"  {job_resp.metadata.namespace} "
                                f"{job_resp.metadata.name}"
                            )
                except ApiException as e:
                    if e.status == 409:
                        print(f"Job {job_name} already exists, skipping")
                    else:
                        raise
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestCreateJobsSkipsSuspended -v`
Expected: PASS — 3 tests.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/k8s/deploy_k8s.py tests/unit/test_job_lifecycle.py
git commit -m "feat: skip suspended jobs in _create_jobs()"
```

---

## Task 6: `_wait_and_stream` helper

**Files:**
- Modify: `stack_orchestrator/deploy/k8s/deploy_k8s.py` (add private method)
- Test: `tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_job_lifecycle.py`:

```python
class FakeLogResponse:
    """Mimics urllib3 HTTPResponse used by kubernetes client log streaming."""

    def __init__(self, chunks):
        self._chunks = chunks

    def stream(self, amt=None, decode_content=True):
        for c in self._chunks:
            yield c

    def release_conn(self):
        pass


class TestWaitAndStream(unittest.TestCase):
    def _deployer(self):
        d = K8sDeployer.__new__(K8sDeployer)
        d.k8s_namespace = "test-ns"
        d.batch_api = MagicMock()
        d.core_api = MagicMock()
        return d

    def _pod(self, phase, name="pod-1"):
        return k8s_client.V1Pod(
            metadata=k8s_client.V1ObjectMeta(name=name),
            status=k8s_client.V1PodStatus(phase=phase),
        )

    def _watch_events(self, *pods):
        for p in pods:
            yield {"type": "MODIFIED", "object": p}

    def test_returns_zero_on_success(self):
        d = self._deployer()
        d.core_api.list_namespaced_pod.return_value = (
            k8s_client.V1PodList(items=[self._pod("Running")])
        )
        d.core_api.read_namespaced_pod_log.return_value = FakeLogResponse(
            [b"hello\n", b"world\n"]
        )
        d.batch_api.read_namespaced_job_status.return_value = (
            k8s_client.V1Job(
                status=k8s_client.V1JobStatus(succeeded=1, failed=0)
            )
        )
        rc = d._wait_and_stream(job_name="j-1", timeout_seconds=0)
        self.assertEqual(rc, 0)

    def test_returns_nonzero_on_failure(self):
        d = self._deployer()
        d.core_api.list_namespaced_pod.return_value = (
            k8s_client.V1PodList(items=[self._pod("Running")])
        )
        d.core_api.read_namespaced_pod_log.return_value = FakeLogResponse(
            [b"boom\n"]
        )
        d.batch_api.read_namespaced_job_status.return_value = (
            k8s_client.V1Job(
                status=k8s_client.V1JobStatus(succeeded=0, failed=1)
            )
        )
        rc = d._wait_and_stream(job_name="j-2", timeout_seconds=0)
        self.assertNotEqual(rc, 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestWaitAndStream -v`
Expected: FAIL with `AttributeError: 'K8sDeployer' object has no attribute '_wait_and_stream'`.

- [ ] **Step 3: Implement `_wait_and_stream`**

In `stack_orchestrator/deploy/k8s/deploy_k8s.py`, add this method to `K8sDeployer` near `run_job` (keep neighbors together):

```python
    def _wait_and_stream(self, job_name: str, timeout_seconds: int) -> int:
        """Block until the Job's pod terminates, streaming logs to stdout.

        Returns 0 if the Job succeeded, non-zero otherwise.

        timeout_seconds=0 means no client-side timeout.
        """
        import sys
        import time

        deadline = (
            time.monotonic() + timeout_seconds
            if timeout_seconds > 0
            else None
        )
        selector = f"job-name={job_name}"

        # Step 1: wait for the pod to appear and leave Pending.
        pod_name = None
        while True:
            if deadline is not None and time.monotonic() > deadline:
                print(
                    f"Timed out waiting for pod of {job_name} to start",
                    file=sys.stderr,
                )
                return 1
            pods = self.core_api.list_namespaced_pod(
                namespace=self.k8s_namespace, label_selector=selector
            )
            if pods.items:
                p = pods.items[0]
                phase = p.status.phase if p.status else None
                if phase and phase != "Pending":
                    pod_name = p.metadata.name
                    break
            time.sleep(1)

        # Step 2: stream logs to stdout (blocking until the pod terminates).
        resp = self.core_api.read_namespaced_pod_log(
            name=pod_name,
            namespace=self.k8s_namespace,
            follow=True,
            _preload_content=False,
        )
        try:
            for chunk in resp.stream(decode_content=True):
                if isinstance(chunk, bytes):
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                else:
                    sys.stdout.write(str(chunk))
                    sys.stdout.flush()
        finally:
            try:
                resp.release_conn()
            except Exception:
                pass

        # Step 3: read final Job status.
        job = self.batch_api.read_namespaced_job_status(
            name=job_name, namespace=self.k8s_namespace
        )
        succeeded = (job.status.succeeded or 0) if job.status else 0
        return 0 if succeeded >= 1 else 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestWaitAndStream -v`
Expected: PASS — 2 tests.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/k8s/deploy_k8s.py tests/unit/test_job_lifecycle.py
git commit -m "feat: _wait_and_stream helper for run-job blocking log stream"
```

---

## Task 7: `K8sDeployer.run_job` — timestamp suffix, extra_env, wait/stream, warning

**Files:**
- Modify: `stack_orchestrator/deploy/k8s/deploy_k8s.py:1623-1660` (the existing `run_job`)
- Test: `tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_job_lifecycle.py`:

```python
class TestRunJob(unittest.TestCase):
    def _deployer(self, jobs):
        d = K8sDeployer.__new__(K8sDeployer)
        d.k8s_namespace = "test-ns"
        d.batch_api = MagicMock()
        d.core_api = MagicMock()
        d.deployment_dir = MagicMock()
        # chart_dir must not exist so we take the non-helm path
        chart_dir = MagicMock()
        chart_dir.exists.return_value = False
        d.deployment_dir.__truediv__.return_value = chart_dir
        d.cluster_info = MagicMock()
        d.cluster_info.app_name = "test-app"
        d.cluster_info.get_jobs.return_value = jobs
        d.type = "k8s-kind"
        # connect_api is called by run_job; stub it out.
        d.connect_api = MagicMock()
        d._wait_and_stream = MagicMock(return_value=0)
        return d

    def test_uses_timestamp_suffix(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=True,
                extra_env={},
                timeout_seconds=0,
            )
        # cluster_info.get_jobs called with the suffix
        kwargs = d.cluster_info.get_jobs.call_args.kwargs
        self.assertEqual(kwargs.get("name_suffix"), "1700000000")

    def test_forwards_extra_env(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=True,
                extra_env={"CHAIN": "gorchain"},
                timeout_seconds=0,
            )
        kwargs = d.cluster_info.get_jobs.call_args.kwargs
        self.assertEqual(kwargs.get("extra_env"), {"CHAIN": "gorchain"})

    def test_warns_for_non_suspended(self):
        not_suspended = _job("test-app-job-warp-deployer", suspended=False)
        d = self._deployer([not_suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock, patch("sys.stderr") as stderr_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "warp-deployer",
                no_wait=True,
                extra_env={},
                timeout_seconds=0,
            )
        written = "".join(
            c.args[0] for c in stderr_mock.write.call_args_list
        )
        self.assertIn("WARNING", written)
        self.assertIn("warp-deployer", written)

    def test_does_not_warn_for_suspended(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock, patch("sys.stderr") as stderr_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=True,
                extra_env={},
                timeout_seconds=0,
            )
        written = "".join(
            c.args[0] for c in stderr_mock.write.call_args_list
        )
        self.assertNotIn("WARNING", written)

    def test_calls_wait_and_stream_unless_no_wait(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=False,
                extra_env={},
                timeout_seconds=0,
            )
        d._wait_and_stream.assert_called_once()

    def test_no_wait_skips_wait_and_stream(self):
        suspended = _job("test-app-job-ism-update", suspended=True)
        d = self._deployer([suspended])
        with patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.opts"
        ) as opts_mock, patch(
            "stack_orchestrator.deploy.k8s.deploy_k8s.time"
        ) as time_mock:
            opts_mock.o.debug = False
            opts_mock.o.dry_run = False
            time_mock.time.return_value = 1700000000.0
            d.run_job(
                "ism-update",
                no_wait=True,
                extra_env={},
                timeout_seconds=0,
            )
        d._wait_and_stream.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestRunJob -v`
Expected: FAIL — current `run_job()` doesn't accept the new kwargs and doesn't add a suffix.

- [ ] **Step 3: Replace `K8sDeployer.run_job`**

At the top of `stack_orchestrator/deploy/k8s/deploy_k8s.py`, ensure these imports are present (add if missing):

```python
import sys
import time
```

Replace the `run_job` method on `K8sDeployer` (currently at ~line 1623):

```python
    def run_job(
        self,
        job_name: str,
        release_name: Optional[str] = None,
        extra_env: Optional[Dict[str, str]] = None,
        no_wait: bool = False,
        timeout_seconds: int = 0,
    ) -> int:
        if opts.o.dry_run:
            return 0

        # Check if this is a helm-based deployment.
        chart_dir = self.deployment_dir / "chart"
        if chart_dir.exists():
            if extra_env:
                raise DeployerException(
                    "--env is not supported on helm-based deployments in v1"
                )
            from stack_orchestrator.deploy.k8s.helm.job_runner import (
                run_helm_job,
            )

            run_helm_job(
                chart_dir=chart_dir,
                job_name=job_name,
                release=release_name,
                namespace=self.k8s_namespace,
                timeout=600,
                verbose=opts.o.verbose,
            )
            return 0

        # Non-Helm path: build a fresh timestamp-suffixed Job.
        self.connect_api()
        suffix = str(int(time.time()))
        job_pull_policy = "IfNotPresent" if self.is_kind() else "Always"
        jobs = self.cluster_info.get_jobs(
            image_pull_policy=job_pull_policy,
            name_suffix=suffix,
            extra_env=extra_env or {},
        )
        base_name = f"{self.cluster_info.app_name}-job-{job_name}"
        target_name = f"{base_name}-{suffix}"
        matched_job = None
        for job in jobs:
            if job.metadata and job.metadata.name == target_name:
                matched_job = job
                break
        if matched_job is None:
            raise DeployerException(
                f"Job '{job_name}' not found. Available base names: "
                f"{[j.metadata.name.rsplit('-', 1)[0] for j in jobs if j.metadata]}"
            )

        labels = (matched_job.metadata.labels or {})
        if labels.get("laconic.suspend") != "true":
            sys.stderr.write(
                f"WARNING: service '{job_name}' is not marked "
                f"laconic.suspend=true. Manually running it may race "
                f"with 'deployment start' auto-creation if the "
                f"deployment has not already started.\n"
            )

        if opts.o.debug:
            print(f"Creating job: {target_name}")
        self.batch_api.create_namespaced_job(
            body=matched_job, namespace=self.k8s_namespace
        )

        if no_wait:
            print(target_name)
            return 0

        return self._wait_and_stream(
            job_name=target_name, timeout_seconds=timeout_seconds
        )
```

> **Notes for implementer:**
> - The existing imports likely include `Optional, Dict` already (verify and add if missing).
> - `DeployerException` is already used in this file — ensure the import line near the top includes it. Look around line 30-40 for the existing import block.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestRunJob -v`
Expected: PASS — 6 tests.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/k8s/deploy_k8s.py tests/unit/test_job_lifecycle.py
git commit -m "feat: K8sDeployer.run_job adds timestamp suffix, extra_env, wait/stream"
```

---

## Task 8: Abstract `Deployer.run_job` signature

**Files:**
- Modify: `stack_orchestrator/deploy/deployer.py:75-77`

- [ ] **Step 1: Update the abstract signature**

In `stack_orchestrator/deploy/deployer.py`, replace:

```python
    @abstractmethod
    def run_job(self, job_name: str, release_name: Optional[str] = None):
        pass
```

with:

```python
    @abstractmethod
    def run_job(
        self,
        job_name: str,
        release_name: Optional[str] = None,
        extra_env: Optional[Dict[str, str]] = None,
        no_wait: bool = False,
        timeout_seconds: int = 0,
    ):
        pass
```

If `Dict` isn't imported at the top of `deployer.py`, add it:

```python
from typing import Dict, Optional
```

(Verify the existing `from typing import …` line; only add `Dict` if absent.)

- [ ] **Step 2: Run existing unit tests to ensure nothing breaks**

Run: `pytest tests/unit/test_job_lifecycle.py -v`
Expected: all tests still PASS — this is signature-only; the k8s deployer implementation already matches.

- [ ] **Step 3: Commit**

```bash
git add stack_orchestrator/deploy/deployer.py
git commit -m "refactor: extend Deployer.run_job abstract signature"
```

---

## Task 9: Docker-compose `run_job` accepts the new kwargs

The docker-compose path does not support `extra_env` or wait/stream in v1. Accept the kwargs to satisfy the abstract signature; warn for `extra_env`; raise for non-default `no_wait` / `timeout_seconds` so operators get a clear message rather than silent no-op.

**Files:**
- Modify: `stack_orchestrator/deploy/compose/deploy_docker.py:153-…` (`run_job`)
- Test: `tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_job_lifecycle.py`:

```python
class TestDockerRunJobKwargs(unittest.TestCase):
    def _docker_deployer(self):
        from stack_orchestrator.deploy.compose.deploy_docker import (
            DockerDeployer,
        )

        d = DockerDeployer.__new__(DockerDeployer)
        d.compose_files = ["/fake/compose/docker-compose.yml"]
        d.compose_project_name = "test"
        d.compose_env_file = None
        return d

    def test_extra_env_warns_but_proceeds(self):
        d = self._docker_deployer()
        with patch(
            "stack_orchestrator.deploy.compose.deploy_docker.opts"
        ) as opts_mock, patch("sys.stderr") as stderr_mock:
            opts_mock.o.dry_run = True
            opts_mock.o.verbose = False
            d.run_job("foo", extra_env={"X": "1"})
        written = "".join(
            c.args[0] for c in stderr_mock.write.call_args_list
        )
        self.assertIn("WARNING", written)

    def test_no_wait_raises(self):
        d = self._docker_deployer()
        from stack_orchestrator.deploy.deployer import DeployerException

        with patch(
            "stack_orchestrator.deploy.compose.deploy_docker.opts"
        ) as opts_mock:
            opts_mock.o.dry_run = True
            with self.assertRaises(DeployerException):
                d.run_job("foo", no_wait=True)

    def test_timeout_raises(self):
        d = self._docker_deployer()
        from stack_orchestrator.deploy.deployer import DeployerException

        with patch(
            "stack_orchestrator.deploy.compose.deploy_docker.opts"
        ) as opts_mock:
            opts_mock.o.dry_run = True
            with self.assertRaises(DeployerException):
                d.run_job("foo", timeout_seconds=30)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestDockerRunJobKwargs -v`
Expected: FAIL — current `run_job` doesn't accept the new kwargs.

- [ ] **Step 3: Modify `DockerDeployer.run_job`**

In `stack_orchestrator/deploy/compose/deploy_docker.py`, replace the `run_job` signature and the top of its body:

```python
    def run_job(
        self,
        job_name: str,
        release_name: Optional[str] = None,
        extra_env: Optional[Dict[str, str]] = None,
        no_wait: bool = False,
        timeout_seconds: int = 0,
    ):
        if no_wait:
            raise DeployerException(
                "--no-wait is not supported on docker-compose deployments"
            )
        if timeout_seconds:
            raise DeployerException(
                "--timeout is not supported on docker-compose deployments"
            )
        if extra_env:
            import sys as _sys

            _sys.stderr.write(
                "WARNING: --env is not supported on docker-compose "
                "deployments; ignoring per-invocation env vars.\n"
            )
        # release_name is ignored for Docker deployments (only used for K8s/Helm)
        if not opts.o.dry_run:
            # ... rest of the existing body unchanged ...
```

If `Dict` is not imported at the top of this file, add it to the `from typing import …` line.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestDockerRunJobKwargs -v`
Expected: PASS — 3 tests.

Re-run the full module:

Run: `pytest tests/unit/test_job_lifecycle.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/compose/deploy_docker.py tests/unit/test_job_lifecycle.py
git commit -m "feat: docker DockerDeployer.run_job accepts new kwargs (warn/raise)"
```

---

## Task 10: `run_job_operation` parses `--env KEY=VAL`

**Files:**
- Modify: `stack_orchestrator/deploy/deploy.py:283-291` (`run_job_operation`)
- Test: `tests/unit/test_job_lifecycle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_job_lifecycle.py`:

```python
class TestParseEnvFlags(unittest.TestCase):
    def test_valid_pairs(self):
        from stack_orchestrator.deploy.deploy import _parse_env_flags

        out = _parse_env_flags(("FOO=bar", "BAZ=quux"))
        self.assertEqual(out, {"FOO": "bar", "BAZ": "quux"})

    def test_empty(self):
        from stack_orchestrator.deploy.deploy import _parse_env_flags

        self.assertEqual(_parse_env_flags(()), {})

    def test_value_with_equals_signs_preserved(self):
        from stack_orchestrator.deploy.deploy import _parse_env_flags

        out = _parse_env_flags(("URL=https://x.y?a=1&b=2",))
        self.assertEqual(out, {"URL": "https://x.y?a=1&b=2"})

    def test_missing_equals_raises(self):
        from stack_orchestrator.deploy.deploy import _parse_env_flags

        with self.assertRaises(ValueError):
            _parse_env_flags(("FOO",))

    def test_empty_key_raises(self):
        from stack_orchestrator.deploy.deploy import _parse_env_flags

        with self.assertRaises(ValueError):
            _parse_env_flags(("=bar",))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_job_lifecycle.py::TestParseEnvFlags -v`
Expected: FAIL with `ImportError: cannot import name '_parse_env_flags'`.

- [ ] **Step 3: Add `_parse_env_flags` and extend `run_job_operation`**

In `stack_orchestrator/deploy/deploy.py`, add the helper near the existing `run_job_operation` (above it, e.g. at line ~282):

```python
def _parse_env_flags(env_args):
    """Parse repeated --env KEY=VAL flag values into a dict.

    Splits on the first '=' only, so values may contain '='.
    Raises ValueError on malformed input.
    """
    parsed = {}
    for item in env_args:
        if "=" not in item:
            raise ValueError(
                f"--env value must be KEY=VAL, got: {item!r}"
            )
        key, value = item.split("=", 1)
        if not key:
            raise ValueError(
                f"--env value has empty key, got: {item!r}"
            )
        parsed[key] = value
    return parsed
```

Replace `run_job_operation` (currently lines 283-291):

```python
def run_job_operation(
    ctx,
    job_name: str,
    helm_release: Optional[str] = None,
    env_args=(),
    no_wait: bool = False,
    timeout_seconds: int = 0,
):
    global_context = ctx.parent.parent.obj
    if global_context.dry_run:
        return
    try:
        extra_env = _parse_env_flags(env_args)
    except ValueError as e:
        print(f"Error parsing --env: {e}")
        sys.exit(2)
    print(f"Running job: {job_name}")
    try:
        rc = ctx.obj.deployer.run_job(
            job_name,
            helm_release,
            extra_env=extra_env,
            no_wait=no_wait,
            timeout_seconds=timeout_seconds,
        )
        if rc:
            sys.exit(rc)
    except Exception as e:
        print(f"Error running job {job_name}: {e}")
        sys.exit(1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_job_lifecycle.py::TestParseEnvFlags -v`
Expected: PASS — 5 tests.

- [ ] **Step 5: Commit**

```bash
git add stack_orchestrator/deploy/deploy.py tests/unit/test_job_lifecycle.py
git commit -m "feat: run_job_operation parses --env KEY=VAL and forwards kwargs"
```

---

## Task 11: Click CLI — `--env`, `--no-wait`, `--timeout`

**Files:**
- Modify: `stack_orchestrator/deploy/deployment.py:258-270` (the `run_job` Click command)

This is wiring; the unit tests in Task 10 already cover the parsing logic. A manual smoke check after the change is sufficient.

- [ ] **Step 1: Replace the Click command**

In `stack_orchestrator/deploy/deployment.py`, replace:

```python
@command.command()
@click.argument("job_name")
@click.option(
    "--helm-release",
    help="Helm release name (for k8s helm chart deployments, defaults to chart name)",
)
@click.pass_context
def run_job(ctx, job_name, helm_release):
    """run a one-time job from the stack"""
    from stack_orchestrator.deploy.deploy import run_job_operation

    ctx.obj = make_deploy_context(ctx)
    run_job_operation(ctx, job_name, helm_release)
```

with:

```python
@command.command()
@click.argument("job_name")
@click.option(
    "--helm-release",
    help="Helm release name (for k8s helm chart deployments, defaults to chart name)",
)
@click.option(
    "--env",
    "envs",
    multiple=True,
    metavar="KEY=VAL",
    help="Per-invocation env var; repeatable, e.g. --env FOO=bar.",
)
@click.option(
    "--no-wait",
    is_flag=True,
    default=False,
    help="Return after Job creation; do not stream logs or wait.",
)
@click.option(
    "--timeout",
    "timeout_seconds",
    type=int,
    default=0,
    help="Seconds to wait before giving up (0 = no timeout). "
         "Ignored with --no-wait.",
)
@click.pass_context
def run_job(ctx, job_name, helm_release, envs, no_wait, timeout_seconds):
    """Run a one-time job from the stack.

    Each invocation creates a fresh timestamp-suffixed Job. Use --env
    to layer per-invocation env vars on top of the compose/spec env.
    By default, blocks streaming the pod's logs to stdout; pass
    --no-wait to return immediately.
    """
    from stack_orchestrator.deploy.deploy import run_job_operation

    ctx.obj = make_deploy_context(ctx)
    run_job_operation(
        ctx,
        job_name,
        helm_release,
        env_args=envs,
        no_wait=no_wait,
        timeout_seconds=timeout_seconds,
    )
```

- [ ] **Step 2: Manual smoke check (help output)**

Run: `laconic-so deployment run-job --help`
Expected: the help output lists `--env`, `--no-wait`, and `--timeout` alongside `--helm-release`. (If `laconic-so` isn't on PATH, run `python -m stack_orchestrator deployment run-job --help` from the repo root.)

- [ ] **Step 3: Run the full unit test module**

Run: `pytest tests/unit/test_job_lifecycle.py -v`
Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add stack_orchestrator/deploy/deployment.py
git commit -m "feat: run-job CLI accepts --env, --no-wait, --timeout"
```

---

## Task 12: Documentation

**Files:**
- Modify: `docs/cli.md`

- [ ] **Step 1: Find the existing `run-job` reference**

Run: `grep -n "run-job" docs/cli.md`
Expected: a small section describing the command. If no such section exists, add a new one in the deployment-commands area (look for `deployment update` or `deployment start` blocks for placement).

- [ ] **Step 2: Replace / append the documentation block**

Replace any existing `run-job` block (or add a new one) with:

````markdown
### `laconic-so deployment run-job`

Run a one-time job from a deployed stack. Each invocation creates a
fresh Kubernetes Job whose name is suffixed with a unix timestamp
(`{app}-job-{name}-{ts}`), so repeated calls do not collide.

```
laconic-so deployment --dir <deploy-dir> run-job <job-name> \
    [--env KEY=VAL ...] \
    [--no-wait] \
    [--timeout SECONDS]
```

**Flags:**

- `--env KEY=VAL` (repeatable) — layer per-invocation env vars on the
  job's container, overriding any same-named entries from compose
  `environment:` or spec `config:`.
- `--no-wait` — return immediately after the Job object is accepted;
  do not stream logs or wait for completion.
- `--timeout SECONDS` — give up waiting after this many seconds
  (default `0` = no timeout). Ignored with `--no-wait`.

**Default behavior:** the command blocks until the Job's pod
terminates, streaming the pod's logs to stdout. Exit code is `0` if
the Job succeeded, non-zero otherwise.

#### Suspending jobs at `deployment start`

A job whose compose service is labeled `laconic.suspend: "true"` is
skipped by `deployment start` — it is only triggered via `run-job`.

```yaml
# compose-jobs/docker-compose-ism-update.yml
services:
  ism-update:
    image: ghcr.io/example/ops:latest
    labels:
      laconic.suspend: "true"
    # …
```

Calling `run-job <name>` on a non-suspended job prints a warning to
stderr (it may race with the auto-create path) but still proceeds.

**Limitations:**
- Helm-based deployments don't support `--env`.
- Docker-compose deployments don't support `--no-wait` or `--timeout`;
  `--env` is ignored with a warning.
````

- [ ] **Step 3: Commit**

```bash
git add docs/cli.md
git commit -m "docs: document laconic.suspend label and run-job flags"
```

---

## Final review

After all tasks complete, the implementer should:

1. Run the full unit test module one more time:

   ```
   pytest tests/unit/test_job_lifecycle.py -v
   ```

   Expected: all tests pass.

2. Run the existing unit tests to confirm nothing regressed:

   ```
   pytest tests/unit/ -v
   ```

   Expected: prior tests still pass.

3. Dispatch a fresh code reviewer subagent (if using
   `subagent-driven-development`) against the diff.

Integration verification (suspended vs non-suspended jobs against
real k8s, log streaming, `--no-wait`, `--timeout`, `--env` end-to-end)
is performed in the **hyperlane-stacks** E2E suite once that PR lands
against the SO change — it requires a live Kind cluster.
