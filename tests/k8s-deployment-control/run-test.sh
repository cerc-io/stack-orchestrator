#!/usr/bin/env bash
set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
    # Dump environment variables for debugging
    echo "Environment variables:"
    env
fi

if [ "$1" == "from-path" ]; then
    TEST_TARGET_SO="laconic-so"
else
    TEST_TARGET_SO=$( ls -t1 ./package/laconic-so* | head -1 )
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
    delete_cluster_exit
}

wait_for_log_output () {
    for i in {1..50}
    do

        local log_output=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )

        if [[ ! -z "$log_output" ]]; then
            # if ready, return
            return
        else
            # if not ready, wait
            sleep 5
        fi
    done
    # Timed out, error exit
    echo "waiting for pods log content: FAILED"
    delete_cluster_exit
}

delete_cluster_exit () {
    $TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes
    exit 1
}

# Set a non-default repo dir
export CERC_REPO_BASE_DIR=~/stack-orchestrator-test/repo-base-dir
echo "Testing this package: $TEST_TARGET_SO"
echo "Test version command"
reported_version_string=$( $TEST_TARGET_SO version )
echo "Version reported is: ${reported_version_string}"
echo "Cloning repositories into: $CERC_REPO_BASE_DIR"
rm -rf $CERC_REPO_BASE_DIR
mkdir -p $CERC_REPO_BASE_DIR
$TEST_TARGET_SO --stack test setup-repositories
$TEST_TARGET_SO --stack test build-containers
# Test basic stack-orchestrator deploy to k8s
test_deployment_dir=$CERC_REPO_BASE_DIR/test-deployment-dir
test_deployment_spec=$CERC_REPO_BASE_DIR/test-deployment-spec.yml

# Create a deployment that we can use to check our test cases
$TEST_TARGET_SO --stack test deploy --deploy-to k8s-kind init --output $test_deployment_spec
# Check the file now exists
if [ ! -f "$test_deployment_spec" ]; then
    echo "deploy init test: spec file not present"
    echo "deploy init test: FAILED"
    exit 1
fi
echo "deploy init test: passed"

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
echo "deploy create output file test: passed"

# At this point the deployment's kind-config.yml will look like this:
# kind: Cluster
# apiVersion: kind.x-k8s.io/v1alpha4
# nodes:
# - role: control-plane
#   kubeadmConfigPatches:
#     - |
#       kind: InitConfiguration
#       nodeRegistration:
#         kubeletExtraArgs:
#           node-labels: "ingress-ready=true"
#   extraPortMappings:
#   - containerPort: 80
#    hostPort: 80

# We need to change it to this:
# Note we also turn up the log level on the scheduler in order to diagnose placement errors
# See logs like: kubectl -n kube-system logs kube-scheduler-laconic-f185cd245d8dba98-control-plane
kind_config_file=${test_deployment_dir}/kind-config.yml
cat << EOF > ${kind_config_file} 
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
kubeadmConfigPatches:
- |
  kind: ClusterConfiguration
  scheduler:
    extraArgs:
      v: "3"
nodes:
- role: control-plane
  kubeadmConfigPatches:
    - |
      kind: InitConfiguration
      nodeRegistration:
        kubeletExtraArgs:
          node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
- role: worker
  labels:
    nodetype: a
- role: worker
  labels:
    nodetype: b
- role: worker
  labels:
    nodetype: c
  kubeadmConfigPatches:
  - |
    kind: JoinConfiguration
    nodeRegistration:
      taints:
        - key: "nodeavoid"
          value: "c"
          effect: "NoSchedule"
EOF

# At this point we should have 4 nodes, three labeled like this:
# $ kubectl get nodes --show-labels=true
# NAME                                     STATUS   ROLES           AGE     VERSION   LABELS
# laconic-3af549a3ba0e3a3c-control-plane   Ready    control-plane   2m37s   v1.30.0   ...,ingress-ready=true
# laconic-3af549a3ba0e3a3c-worker          Ready    <none>          2m18s   v1.30.0   ...,nodetype=a
# laconic-3af549a3ba0e3a3c-worker2         Ready    <none>          2m18s   v1.30.0   ...,nodetype=b
# laconic-3af549a3ba0e3a3c-worker3         Ready    <none>          2m18s   v1.30.0   ...,nodetype=c

# And with taints like this:
# $ kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints --no-headers
# laconic-3af549a3ba0e3a3c-control-plane   [map[effect:NoSchedule key:node-role.kubernetes.io/control-plane]]
# laconic-3af549a3ba0e3a3c-worker          <none>
# laconic-3af549a3ba0e3a3c-worker2         <none>
# laconic-3af549a3ba0e3a3c-worker3         [map[effect:NoSchedule key:nodeavoid value:c]]

# We can now modify the deployment spec file to require a set of affinity and/or taint combinations
# then bring up the deployment and check that the pod is scheduled to an expected node.

# Add a requirement to schedule on a node labeled nodetype=c and
# a toleration such that no other pods schedule on that node
deployment_spec_file=${test_deployment_dir}/spec.yml
cat << EOF >> ${deployment_spec_file}
node-affinities:
  - label: nodetype
    value: c
node-tolerations:
  - key: nodeavoid
    value: c
EOF

# Get the deployment ID so we can generate low level kubectl commands later
deployment_id=$(cat ${test_deployment_dir}/deployment.yml | cut -d ' ' -f 2)

# Try to start the deployment
$TEST_TARGET_SO deployment --dir $test_deployment_dir start
wait_for_pods_started
# Check logs command works
wait_for_log_output
sleep 1
log_output_1=$( $TEST_TARGET_SO deployment --dir $test_deployment_dir logs )
if [[ "$log_output_1" == *"filesystem is fresh"* ]]; then
    echo "deployment of pod test: passed"
else
    echo "deployment pod test: FAILED"
    echo $log_output_1
    delete_cluster_exit
fi

# The deployment's pod should be scheduled onto node: worker3
# Check that's what happened
# Get get the node onto which the stack pod has been deployed
deployment_node=$(kubectl get pods -l app=${deployment_id} -o=jsonpath='{.items..spec.nodeName}')
expected_node=${deployment_id}-worker3
echo "Stack pod deployed to node: ${deployment_node}"
if [[ ${deployment_node} == ${expected_node} ]]; then
    echo "deployment of pod test: passed"
else
    echo "deployment pod test: FAILED"
    echo "Stack pod deployed to node: ${deployment_node}, expected node: ${expected_node}"
    delete_cluster_exit
fi

# Stop and clean up
$TEST_TARGET_SO deployment --dir $test_deployment_dir stop --delete-volumes
echo "Test passed"
