# Stack Orchestrator TODO

## Pending Features

### k8s cluster management

- [ ] Add command to remove unused/empty laconic-* kind clusters
  - Should detect clusters with no deployments running
  - Command: `laconic-so deploy k8s delete cluster` or similar
  - Safety: prompt for confirmation before deletion
