#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
    # Dump environment variables for debugging
    echo "Environment variables:"
    env
fi

# Helper functions: TODO move into a separate file
wait_for_pods_started () {
    for i in {1..50}
    do
        local ps_output=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir ps )

        if [[ "$ps_output" == *"Running containers:"* ]]; then
            # if ready, return
            return
        else
            # if not ready, wait
            sleep 5
        fi
    done
    # Timed out, error exit
    echo "waiting for pods to start: FAILED"
    cleanup_and_exit
}

wait_for_log_output () {
    for i in {1..50}
    do

        local log_output=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )

        if [[ ! -z "$log_output" ]] && [[ "$log_output" != *"No logs available"* ]] && [[ "$log_output" != *"Pods not running"* ]]; then
            # if ready, return
            return
        else
            # if not ready, wait
            sleep 5
        fi
    done
    # Timed out, error exit
    echo "waiting for pods log content: FAILED"
    cleanup_and_exit
}


cleanup_and_exit () {
    # Full teardown so CI runners don't leak namespaces/PVs between runs.
    $TEST_TARGET_SO deployment --dir $test_deployment_dir \
        stop --delete-volumes --delete-namespace --skip-cluster-management || true
    exit 1
}

assert_ns_phase () {
    local expected=$1
    local phase
    phase=$(kubectl get namespace ${deployment_ns} -o jsonpath='{.status.phase}' 2>/dev/null || echo "Missing")
    if [ "$phase" != "$expected" ]; then
        echo "namespace phase test: FAILED (expected ${expected}, got ${phase})"
        cleanup_and_exit
    fi
}

# Count labeled resources in the deployment namespace. down() is
# synchronous on its own cleanup (waits for PVCs/pods to terminate
# before returning) so callers can assert immediately.
# Usage: assert_no_labeled_resources <kind>
assert_no_labeled_resources () {
    local kind=$1
    local count
    count=$(kubectl get ${kind} -n ${deployment_ns} \
        -l app.kubernetes.io/stack=test --no-headers 2>/dev/null | wc -l)
    if [ "$count" -ne 0 ]; then
        echo "labeled cleanup test: FAILED (${kind} still present: ${count})"
        cleanup_and_exit
    fi
}

# Note: eventually this test should be folded into ../deploy/
# but keeping it separate for now for convenience
TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
# Set a non-default repo dir
export CERC_REPO_BASE_DIR=~/stack-orchestrator-test/repo-base-dir
# kind-mount-root is cluster-level infra, independent of any deployment dir.
# Previous runs' CronJob wrote files here as root via the Kind bind mount.
export KIND_MOUNT_ROOT=~/stack-orchestrator-test/kind-mount
echo "Testing this package: $TEST_TARGET_SO"
echo "Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "Version reported is: ${reported_version_string}"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
rm -rf $CERC_REPO_BASE_DIR
mkdir -p $CERC_REPO_BASE_DIR
sudo rm -rf $KIND_MOUNT_ROOT
mkdir -p $KIND_MOUNT_ROOT
$TEST_TARGET_SO --stack test setup-repositories
$TEST_TARGET_SO --stack test build-containers
# Test basic stack-orchestrator deploy to k8s
test_deployment_dir=$CERC_REPO_BASE_DIR/test-deployment-dir
test_deployment_spec=$CERC_REPO_BASE_DIR/test-deployment-spec.yml
$TEST_TARGET_SO --stack test deploy --deploy-to k8s-kind init --output $test_deployment_spec --config CERC_TEST_PARAM_1=PASSED
# Check the file now exists
if [ ! -f "$test_deployment_spec" ]; then
    echo "deploy init test: spec file not present"
    echo "deploy init test: FAILED"
    exit 1
fi
echo "deploy init test: passed"

# Switch to a full path for bind mount.
sed -i "s|^\(\s*test-data-bind:$\)$|\1 ${test_deployment_dir}/data/test-data-bind|" $test_deployment_spec

# Enable caddy cert backup by setting kind-mount-root.
echo "kind-mount-root: $KIND_MOUNT_ROOT" >> $test_deployment_spec

$TEST_TARGET_SO --stack test deploy create --spec-file $test_deployment_spec --deployment-dir $test_deployment_dir
# Check the deployment dir exists
if [ ! -d "$test_deployment_dir" ]; then
    echo "deploy create test: deployment directory not present"
    echo "deploy create test: FAILED"
    exit 1
fi
echo "deploy create test: passed"
# Check the file writted by the create command in the stack now exists
if [ ! -f "$test_deployment_dir/create-file" ]; then
    echo "deploy create test: create output file not present"
    echo "deploy create test: FAILED"
    exit 1
fi
# And has the right content
create_file_content=$(<$test_deployment_dir/create-file)
if [ ! "$create_file_content" == "create-command-output-data"  ]; then
    echo "deploy create test: create output file contents not correct"
    echo "deploy create test: FAILED"
    exit 1
fi

# Add a config file to be picked up by the ConfigMap before starting.
echo "dbfc7a4d-44a7-416d-b5f3-29842cc47650" > $test_deployment_dir/configmaps/test-config/test_config

# Add secrets to the deployment spec (references a pre-existing k8s Secret by name).
# deploy init already writes an empty 'secrets: {}' key, so we replace it
# rather than appending (ruamel.yaml rejects duplicate keys).
deployment_spec_file=${test_deployment_dir}/spec.yml
sed -i 's/^secrets: {}$/secrets:\n  test-secret:\n    - TEST_SECRET_KEY/' ${deployment_spec_file}

# Get the deployment ID and namespace for kubectl queries
deployment_id=$(cat ${test_deployment_dir}/deployment.yml | cut -d ' ' -f 2)
# Namespace is derived from stack name: laconic-{stack_name}
deployment_ns="laconic-test"

echo "deploy create output file test: passed"
# Try to start the deployment (--perform-cluster-management needed on first start
# because 'start' defaults to --skip-cluster-management)
$TEST_TARGET_SO deployment --dir $test_deployment_dir start --perform-cluster-management
wait_for_pods_started

# Caddy cert backup install: CronJob + RBAC should exist in caddy-system
for kind in serviceaccount role rolebinding cronjob; do
    if ! kubectl get $kind caddy-cert-backup -n caddy-system >/dev/null 2>&1; then
        echo "caddy-cert-backup $kind install test: FAILED"
        cleanup_and_exit
    fi
done
echo "caddy-cert-backup install test: passed"

# Check logs command works
wait_for_log_output
sleep 1
log_output_3=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_3" == *"filesystem is fresh"* ]]; then
    echo "deployment logs test: passed"
else
    echo "deployment logs test: FAILED"
    echo "$log_output_3"
    cleanup_and_exit
fi

# Check the config variable CERC_TEST_PARAM_1 was passed correctly
if [[ "$log_output_3" == *"Test-param-1: PASSED"* ]]; then
    echo "deployment config test: passed"
else
    echo "deployment config test: FAILED"
    cleanup_and_exit
fi

# Check the config variable CERC_TEST_PARAM_2 was passed correctly from the compose file
if [[ "$log_output_3" == *"Test-param-2: CERC_TEST_PARAM_2_VALUE"* ]]; then
    echo "deployment compose config test: passed"
else
    echo "deployment compose config test: FAILED"
    exit 1
fi

# Check that the ConfigMap is mounted and contains the expected content.
log_output_4=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_4" == *"/config/test_config:"* ]] && [[ "$log_output_4" == *"dbfc7a4d-44a7-416d-b5f3-29842cc47650"* ]]; then
    echo "deployment ConfigMap test: passed"
else
    echo "deployment ConfigMap test: FAILED"
    cleanup_and_exit
fi

# Check that the bind-mount volume is mounted.
log_output_5=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_5" == *"/data: MOUNTED"* ]]; then
    echo "deployment bind volumes test: passed"
else
    echo "deployment bind volumes test: FAILED"
    echo "$log_output_5"
    cleanup_and_exit
fi

# Check that the provisioner managed volume is mounted.
log_output_6=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_6" == *"/data2: MOUNTED"* ]]; then
    echo "deployment provisioner volumes test: passed"
else
    echo "deployment provisioner volumes test: FAILED"
    echo "$log_output_6"
    cleanup_and_exit
fi

# --- New feature tests: namespace, labels, jobs, secrets ---

# Check that the pod is in the deployment-specific namespace (not default)
ns_pod_count=$(kubectl get pods -n ${deployment_ns} -l app=${deployment_id} --no-headers 2>/dev/null | wc -l)
if [ "$ns_pod_count" -gt 0 ]; then
    echo "namespace isolation test: passed"
else
    echo "namespace isolation test: FAILED"
    echo "Expected pod in namespace ${deployment_ns}"
    cleanup_and_exit
fi

# Check that the stack label is set on the pod
stack_label_count=$(kubectl get pods -n ${deployment_ns} -l app.kubernetes.io/stack=test --no-headers 2>/dev/null | wc -l)
if [ "$stack_label_count" -gt 0 ]; then
    echo "stack label test: passed"
else
    echo "stack label test: FAILED"
    cleanup_and_exit
fi

# Check that the job completed successfully
for i in {1..30}; do
    job_status=$(kubectl get job ${deployment_id}-job-test-job -n ${deployment_ns} -o jsonpath='{.status.succeeded}' 2>/dev/null || true)
    if [ "$job_status" == "1" ]; then
        break
    fi
    sleep 2
done
if [ "$job_status" == "1" ]; then
    echo "job completion test: passed"
else
    echo "job completion test: FAILED"
    echo "Job status.succeeded: ${job_status}"
    cleanup_and_exit
fi

# Check that the secrets spec results in an envFrom secretRef on the pod
secret_ref=$(kubectl get pod -n ${deployment_ns} -l app=${deployment_id} \
    -o jsonpath='{.items[0].spec.containers[0].envFrom[?(@.secretRef.name=="test-secret")].secretRef.name}' 2>/dev/null || true)
if [ "$secret_ref" == "test-secret" ]; then
    echo "secrets envFrom test: passed"
else
    echo "secrets envFrom test: FAILED"
    echo "Expected secretRef 'test-secret', got: ${secret_ref}"
    cleanup_and_exit
fi

# Stop with --delete-volumes (but not --delete-namespace) and verify:
#   - namespace stays Active (no termination race on restart)
#   - stack-labeled workloads are gone
#   - bind-mount data on the host survives; provisioner volumes are recreated
$TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes --skip-cluster-management

assert_ns_phase "Active"
echo "stop preserves namespace test: passed"

for kind in deployment job ingress service configmap secret pvc pod; do
    assert_no_labeled_resources "$kind"
done
echo "stop cleans labeled resources test: passed"

# Restart — no wait needed, the namespace is still Active.
$TEST_TARGET_SO deployment --dir $test_deployment_dir start --skip-cluster-management
wait_for_pods_started
wait_for_log_output
sleep 1

log_output_10=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_10" == *"/data filesystem is old"* ]]; then
    echo "Retain bind volumes test: passed"
else
    echo "Retain bind volumes test: FAILED"
    cleanup_and_exit
fi

# Provisioner volumes are destroyed when PVs are deleted (--delete-volumes on stop).
# Unlike bind-mount volumes whose data persists on the host, provisioner storage
# is gone, so the volume appears fresh after restart.
log_output_11=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_11" == *"/data2 filesystem is fresh"* ]]; then
    echo "Fresh provisioner volumes test: passed"
else
    echo "Fresh provisioner volumes test: FAILED"
    cleanup_and_exit
fi

# --- Caddy cert backup/restore E2E ---
# Seed a fake cert secret in caddy-system (simulates an LE-issued cert).
fake_cert_name="caddy.ingress--certificates.test-domain.test-domain.crt"
fake_cert_value="fake-cert-$(date +%s)"
kubectl create secret generic "$fake_cert_name" \
    -n caddy-system \
    --from-literal=value="$fake_cert_value"
kubectl label secret "$fake_cert_name" -n caddy-system manager=caddy

# Trigger the CronJob immediately (it fires every 5min on its own).
kubectl create job --from=cronjob/caddy-cert-backup \
    caddy-cert-backup-manual -n caddy-system
kubectl wait --for=condition=complete \
    job/caddy-cert-backup-manual -n caddy-system --timeout=60s

# Backup file is root-owned (CronJob writes as root via kind bind mount).
backup_file=$KIND_MOUNT_ROOT/caddy-cert-backup/caddy-secrets.yaml
if ! sudo test -f "$backup_file"; then
    echo "caddy cert backup file test: FAILED (missing $backup_file)"
    cleanup_and_exit
fi
if ! sudo grep -q "$fake_cert_value" "$backup_file"; then
    echo "caddy cert backup content test: FAILED (value not found in backup)"
    cleanup_and_exit
fi
echo "caddy cert backup write test: passed"

# Full teardown including Kind cluster — --perform-cluster-management on stop
# destroys the cluster, simulating the "recreate from scratch" scenario.
$TEST_TARGET_SO deployment --dir $test_deployment_dir \
    stop --delete-volumes --delete-namespace --perform-cluster-management

# Recreate: new Kind cluster, Caddy install should restore from backup BEFORE
# the Caddy Deployment pod starts.
$TEST_TARGET_SO deployment --dir $test_deployment_dir start --perform-cluster-management
wait_for_pods_started

if ! kubectl get secret "$fake_cert_name" -n caddy-system >/dev/null 2>&1; then
    echo "caddy cert restore test: FAILED (secret missing from new cluster)"
    cleanup_and_exit
fi
restored_value=$(kubectl get secret "$fake_cert_name" -n caddy-system \
    -o jsonpath='{.data.value}' | base64 -d)
if [ "$restored_value" != "$fake_cert_value" ]; then
    echo "caddy cert restore test: FAILED (value mismatch: '$restored_value')"
    cleanup_and_exit
fi
echo "caddy cert restore test: passed"

# Final teardown: --delete-namespace nukes the namespace after labeled cleanup.
# Verify the namespace is actually gone.
$TEST_TARGET_SO deployment --dir $test_deployment_dir \
    stop --delete-volumes --delete-namespace --skip-cluster-management
if kubectl get namespace ${deployment_ns} >/dev/null 2>&1; then
    echo "delete-namespace test: FAILED (namespace still present)"
    exit 1
fi
echo "delete-namespace test: passed"

echo "Test passed"
