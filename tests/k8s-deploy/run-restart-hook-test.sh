#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
    echo "Environment variables:"
    env
fi

# Helper functions: TODO move into a separate file (mirrors run-deploy-test.sh:10).
wait_for_pods_started () {
    local dir=$1
    for i in {1..50}
    do
        local ps_output=$( $TEST_TARGET_SO deployment --dir $dir ps )

        if [[ "$ps_output" == *"Running containers:"* ]]; then
            return
        else
            sleep 5
        fi
    done
    echo "waiting for pods to start: FAILED"
    cleanup_and_exit
}

# Multi-pod stacks aren't visible to 'deployment ps' (deploy_k8s.py:1366
# filters by app_name-deployment substring, which doesn't match
# laconic-<id>-<podname>-deployment-<hash> names). Wait via kubectl.
wait_for_k8s_pods_ready () {
    local ns=$1
    local timeout=240
    local waited=0
    # First wait for at least one pod to appear in the namespace.
    while [ $waited -lt $timeout ]; do
        local count=$(kubectl get pods -n "$ns" --no-headers 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            break
        fi
        sleep 2
        waited=$((waited + 2))
    done
    if ! kubectl wait --for=condition=Ready pod --all \
            -n "$ns" --timeout=$((timeout - waited))s 2>&1; then
        echo "kubectl wait pods ready: FAILED (ns=$ns)"
        kubectl get pods -n "$ns" 2>&1 || true
        kubectl describe pods -n "$ns" 2>&1 | tail -80 || true
        cleanup_and_exit
    fi
}

# Best-effort full teardown so CI runners don't leak namespaces/PVs/clusters
# between runs. Variables may be unset depending on which phase tripped.
cleanup_and_exit () {
    if [ -n "$DEP1" ] && [ -d "$DEP1" ]; then
        $TEST_TARGET_SO deployment --dir $DEP1 \
            stop --delete-volumes --delete-namespace --skip-cluster-management || true
    fi
    if [ -n "$DEP2" ] && [ -d "$DEP2" ]; then
        $TEST_TARGET_SO deployment --dir $DEP2 \
            stop --delete-volumes --delete-namespace --perform-cluster-management || true
    fi
    exit 1
}

# Make a clone usable for `git commit` without touching the runner's global config.
configure_git_identity () {
    local repo_dir=$1
    git -C $repo_dir config user.email "test@stack-orchestrator.test"
    git -C $repo_dir config user.name "test"
}

TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
echo "Testing this package: $TEST_TARGET_SO"

WORK_DIR=~/stack-orchestrator-test/restart-hook
# Multi-repo pod working clones land here; resolved by get_plugin_code_paths.
export CERC_REPO_BASE_DIR=$WORK_DIR/repo-base
rm -rf $WORK_DIR
mkdir -p $WORK_DIR $CERC_REPO_BASE_DIR

# Source location of the test stacks shipped in this checkout. The test stages
# them into a temp git repo so 'deployment restart' (which runs 'git pull' on
# the stack source) has a real repo to pull from.
DATA_DIR=stack_orchestrator/data

# ============================================================================
# Phase 1 — single-repo restart cycle. Verifies that:
#   * deploy create copies commands.py into <deployment>/hooks/
#   * deployment start runs the copied start() hook
#   * mutating the stack-source commands.py and running 'deployment restart'
#     re-copies the new file into hooks/ and re-executes the new start()
# ============================================================================
echo "=== Phase 1: single-repo restart cycle ==="

BARE1=$WORK_DIR/stack-single.git
CLONE1=$WORK_DIR/stack-single
git init -b main --bare $BARE1
git clone $BARE1 $CLONE1
configure_git_identity $CLONE1

# External-stack layout: <repo>/stack-orchestrator/{stacks,compose}/...
mkdir -p $CLONE1/stack-orchestrator/stacks $CLONE1/stack-orchestrator/compose
cp -r $DATA_DIR/stacks/test-restart-hook $CLONE1/stack-orchestrator/stacks/
cp $DATA_DIR/compose/docker-compose-test-restart-hook.yml $CLONE1/stack-orchestrator/compose/

git -C $CLONE1 add .
git -C $CLONE1 commit -m "test-restart-hook v1"
git -C $CLONE1 push -u origin main

STACK_PATH_SINGLE=$CLONE1/stack-orchestrator/stacks/test-restart-hook
SPEC1=$WORK_DIR/spec-single.yml
DEP1=$WORK_DIR/dep-single

$TEST_TARGET_SO --stack $STACK_PATH_SINGLE deploy --deploy-to k8s-kind init --output $SPEC1
$TEST_TARGET_SO --stack $STACK_PATH_SINGLE deploy create --spec-file $SPEC1 --deployment-dir $DEP1

if [ ! -f "$DEP1/hooks/commands.py" ]; then
    echo "single-repo deploy create test: FAILED (hooks/commands.py missing)"
    cleanup_and_exit
fi
if ! grep -q '"v1"' "$DEP1/hooks/commands.py"; then
    echo "single-repo deploy create test: FAILED (hooks/commands.py does not contain v1 marker)"
    cleanup_and_exit
fi
echo "single-repo deploy create test: passed"

$TEST_TARGET_SO deployment --dir $DEP1 start --perform-cluster-management
wait_for_pods_started $DEP1

# call_stack_deploy_start runs synchronously inside the start command
# (deploy_k8s.py:1026), so the marker is on disk before 'start' returns.
if [ ! -f "$DEP1/start-hook-marker" ]; then
    echo "single-repo start hook v1 test: FAILED (marker file missing)"
    cleanup_and_exit
fi
marker_v1=$(cat $DEP1/start-hook-marker)
if [ "$marker_v1" != "v1" ]; then
    echo "single-repo start hook v1 test: FAILED (got: $marker_v1)"
    cleanup_and_exit
fi
echo "single-repo start hook v1 test: passed"

# Mutate the stack-source working tree v1 -> v2. No commit needed: 'deployment
# restart' runs 'git pull' against the bare which is a no-op, and _copy_hooks
# reads the working tree directly via get_plugin_code_paths.
sed -i 's/"v1"/"v2"/' $STACK_PATH_SINGLE/deploy/commands.py

$TEST_TARGET_SO deployment --dir $DEP1 restart --stack-path $STACK_PATH_SINGLE

if ! grep -q '"v2"' "$DEP1/hooks/commands.py"; then
    echo "single-repo restart hook re-copy test: FAILED (hooks/commands.py still v1)"
    cleanup_and_exit
fi
echo "single-repo restart hook re-copy test: passed"

marker_v2=$(cat $DEP1/start-hook-marker)
if [ "$marker_v2" != "v2" ]; then
    echo "single-repo restart hook re-execute test: FAILED (got: $marker_v2)"
    cleanup_and_exit
fi
echo "single-repo restart hook re-execute test: passed"

# Stop phase 1 deployment but keep the cluster for phase 2.
$TEST_TARGET_SO deployment --dir $DEP1 \
    stop --delete-volumes --delete-namespace --skip-cluster-management

# ============================================================================
# Phase 2 — multi-repo create + start. Verifies that a stack with N pods, each
# from a separate repo, produces hooks/commands_0.py ... commands_{N-1}.py and
# that call_stack_deploy_start invokes every module's start().
# ============================================================================
echo "=== Phase 2: multi-repo create + start ==="

# Pod repos: stack.yml's pods[].repository = 'cerc-io/test-restart-hook-pod-X'
# resolves (via get_plugin_code_paths) to
# $CERC_REPO_BASE_DIR/test-restart-hook-pod-X/<pod_path>/stack/...
for label in a b; do
    POD_BARE=$WORK_DIR/pod-$label.git
    POD_CLONE=$CERC_REPO_BASE_DIR/test-restart-hook-pod-$label
    git init -b main --bare $POD_BARE
    git clone $POD_BARE $POD_CLONE
    configure_git_identity $POD_CLONE
    mkdir -p $POD_CLONE/stack/deploy
    # For dict-form pods, get_pod_file_path resolves the compose file at
    # <pod_repo>/<pod_path>/docker-compose.yml — owned by the pod repo, not
    # the stack repo. get_plugin_code_paths adds the trailing 'stack/', so
    # commands.py lives at <pod_repo>/<pod_path>/stack/deploy/commands.py.
    cat > $POD_CLONE/docker-compose.yml <<EOF
services:
  test-restart-hook-multi-$label:
    image: busybox:1.36
    command: ["sh", "-c", "sleep infinity"]
    restart: always
EOF
    # Each pod hook writes a distinct marker file so neither overwrites the
    # other when both start() hooks are loaded by call_stack_deploy_start.
    cat > $POD_CLONE/stack/deploy/commands.py <<EOF
from stack_orchestrator.deploy.deployment_context import DeploymentContext


def start(deployment_context: DeploymentContext):
    marker = deployment_context.deployment_dir / "start-hook-marker-$label"
    marker.write_text("v1")
EOF
    git -C $POD_CLONE add .
    git -C $POD_CLONE commit -m "pod $label v1"
    git -C $POD_CLONE push -u origin main
done

# Stack repo
BARE2=$WORK_DIR/stack-multi.git
CLONE2=$WORK_DIR/stack-multi
git init -b main --bare $BARE2
git clone $BARE2 $CLONE2
configure_git_identity $CLONE2

# For multi-repo (dict-form pods), the stack repo only owns stack.yml — pod
# compose files and hooks live in the per-pod repos under CERC_REPO_BASE_DIR.
mkdir -p $CLONE2/stack-orchestrator/stacks
cp -r $DATA_DIR/stacks/test-restart-hook-multi $CLONE2/stack-orchestrator/stacks/

git -C $CLONE2 add .
git -C $CLONE2 commit -m "test-restart-hook-multi v1"
git -C $CLONE2 push -u origin main

STACK_PATH_MULTI=$CLONE2/stack-orchestrator/stacks/test-restart-hook-multi
SPEC2=$WORK_DIR/spec-multi.yml
DEP2=$WORK_DIR/dep-multi

$TEST_TARGET_SO --stack $STACK_PATH_MULTI deploy --deploy-to k8s-kind init --output $SPEC2
$TEST_TARGET_SO --stack $STACK_PATH_MULTI deploy create --spec-file $SPEC2 --deployment-dir $DEP2

# get_plugin_code_paths returns list(set(...)) so the index ordering is not
# guaranteed; we assert presence of both files rather than mapping each to
# a specific pod.
if [ ! -f "$DEP2/hooks/commands_0.py" ] || [ ! -f "$DEP2/hooks/commands_1.py" ]; then
    echo "multi-repo deploy create test: FAILED (hooks/commands_{0,1}.py missing)"
    ls -la $DEP2/hooks/ || true
    cleanup_and_exit
fi
echo "multi-repo deploy create test: passed"

$TEST_TARGET_SO deployment --dir $DEP2 start --skip-cluster-management
wait_for_k8s_pods_ready laconic-test-restart-hook-multi

for label in a b; do
    if [ ! -f "$DEP2/start-hook-marker-$label" ]; then
        echo "multi-repo start hook test: FAILED (start-hook-marker-$label missing)"
        cleanup_and_exit
    fi
    val=$(cat $DEP2/start-hook-marker-$label)
    if [ "$val" != "v1" ]; then
        echo "multi-repo start hook test: FAILED (start-hook-marker-$label content: $val)"
        cleanup_and_exit
    fi
done
echo "multi-repo start hook test: passed"

# Final teardown — destroy the cluster for the next CI run.
$TEST_TARGET_SO deployment --dir $DEP2 \
    stop --delete-volumes --delete-namespace --perform-cluster-management

rm -rf $WORK_DIR

echo "Test passed"
