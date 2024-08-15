# K8S Deployment Enhancements
## Controlling pod placement
The placement of pods created as part of a stack deployment can be controlled to either avoid certain nodes, or require certain nodes.
### Pod/Node Affinity
Node affinity rules applied to pods target node labels. The effect is that a pod can only be placed on a node having the specified label value. Note that other pods that do not have any node affinity rules can also be placed on those same nodes. Thus node affinity for a pod controls where that pod can be placed, but does not control where other pods are placed.

Node affinity for stack pods is specified in the deployment's `spec.yml` file as follows:
```
node-affinities:
  - label: nodetype
    value: typeb
```
This example denotes that the stack's pods should only be placed on nodes that have the label `nodetype` with value `typeb`.
### Node Taint Toleration
K8s nodes can be given one or more "taints". These are special fields (distinct from labels) with a name (key) and optional value.
When placing pods, the k8s scheduler will only assign a pod to a tainted node if the pod posesses a corresponding "toleration".
This is metadata associated with the pod that specifies that the pod "tolerates" a given taint.
Therefore taint toleration provides a mechanism by which only certain pods can be placed on specific nodes, and provides a complementary mechanism to node affinity.

Taint toleration for stack pods is specified in the deployment's `spec.yml` file as follows:
```
node-tolerations:
  - key: nodetype
    value: typeb
```
This example denotes that the stack's pods will tolerate a taint: `nodetype=typeb`

