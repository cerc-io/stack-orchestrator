# Docker Compose Deployment Guide

## Introduction

### What is a Deployer?

In stack-orchestrator, a **deployer** provides a uniform interface for orchestrating containerized applications. This guide focuses on Docker Compose deployments, which is the default and recommended deployment mode.

While stack-orchestrator also supports Kubernetes (`k8s`) and Kind (`k8s-kind`) deployments, those are out of scope for this guide. See the [Kubernetes Enhancements](./k8s-deployment-enhancements.md) documentation for advanced deployment options.

## Prerequisites

To deploy stacks using Docker Compose, you need:

- Docker Engine (20.10+)
- Docker Compose plugin (v2.0+)
- Python 3.8+
- stack-orchestrator installed (`laconic-so`)

**That's it!** No additional infrastructure is required. If you have Docker installed, you're ready to deploy.

## Deployment Workflow

The typical deployment workflow consists of four main steps:

1. **Setup repositories and build containers** (first time only)
2. **Initialize deployment specification**
3. **Create deployment directory**
4. **Start and manage services**

## Quick Start Example

Here's a complete example using the built-in `test` stack:

```bash
# Step 1: Setup (first time only)
laconic-so --stack test setup-repositories
laconic-so --stack test build-containers

# Step 2: Initialize deployment spec
laconic-so --stack test deploy init --output test-spec.yml

# Step 3: Create deployment directory
laconic-so --stack test deploy create \
  --spec-file test-spec.yml \
  --deployment-dir test-deployment

# Step 4: Start services
laconic-so deployment --dir test-deployment start

# View running services
laconic-so deployment --dir test-deployment ps

# View logs
laconic-so deployment --dir test-deployment logs

# Stop services (preserves data)
laconic-so deployment --dir test-deployment stop
```

## Deployment Workflows

Stack-orchestrator supports two deployment workflows:

### 1. Deployment Directory Workflow (Recommended)

This workflow creates a persistent deployment directory that contains all configuration and data.

**When to use:**
- Production deployments
- When you need to preserve configuration
- When you want to manage multiple deployments
- When you need persistent volume data

**Example:**

```bash
# Initialize deployment spec
laconic-so --stack fixturenet-eth deploy init --output eth-spec.yml

# Optionally edit eth-spec.yml to customize configuration

# Create deployment directory
laconic-so --stack fixturenet-eth deploy create \
  --spec-file eth-spec.yml \
  --deployment-dir my-eth-deployment

# Start the deployment
laconic-so deployment --dir my-eth-deployment start

# Manage the deployment
laconic-so deployment --dir my-eth-deployment ps
laconic-so deployment --dir my-eth-deployment logs
laconic-so deployment --dir my-eth-deployment stop
```

### 2. Quick Deploy Workflow

This workflow deploys directly without creating a persistent deployment directory.

**When to use:**
- Quick testing
- Temporary deployments
- Simple stacks that don't require customization

**Example:**

```bash
# Start the stack directly
laconic-so --stack test deploy up

# Check service status
laconic-so --stack test deploy port test 80

# View logs
laconic-so --stack test deploy logs

# Stop (preserves volumes)
laconic-so --stack test deploy down

# Stop and remove volumes
laconic-so --stack test deploy down --delete-volumes
```

## Real-World Example: Ethereum Fixturenet

Deploy a local Ethereum testnet with Geth and Lighthouse:

```bash
# Setup (first time only)
laconic-so --stack fixturenet-eth setup-repositories
laconic-so --stack fixturenet-eth build-containers

# Initialize with default configuration
laconic-so --stack fixturenet-eth deploy init --output eth-spec.yml

# Create deployment
laconic-so --stack fixturenet-eth deploy create \
  --spec-file eth-spec.yml \
  --deployment-dir fixturenet-eth-deployment

# Start the network
laconic-so deployment --dir fixturenet-eth-deployment start

# Check status
laconic-so deployment --dir fixturenet-eth-deployment ps

# Access logs from specific service
laconic-so deployment --dir fixturenet-eth-deployment logs fixturenet-eth-geth-1

# Stop the network (preserves blockchain data)
laconic-so deployment --dir fixturenet-eth-deployment stop

# Start again - blockchain data is preserved
laconic-so deployment --dir fixturenet-eth-deployment start

# Clean up everything including data
laconic-so deployment --dir fixturenet-eth-deployment stop --delete-volumes
```

## Configuration

### Passing Configuration Parameters

Configuration can be passed in three ways:

**1. At init time via `--config` flag:**

```bash
laconic-so --stack test deploy init --output spec.yml \
  --config PARAM1=value1,PARAM2=value2
```

**2. Edit the spec file after init:**

```bash
# Initialize
laconic-so --stack test deploy init --output spec.yml

# Edit spec.yml
vim spec.yml
```

Example spec.yml:
```yaml
stack: test
config:
  PARAM1: value1
  PARAM2: value2
```

**3. Docker Compose defaults:**

Environment variables defined in the stack's `docker-compose-*.yml` files are used as defaults. Configuration from the spec file overrides these defaults.

### Port Mapping

By default, services are accessible on randomly assigned host ports. To find the mapped port:

```bash
# Find the host port for container port 80 on service 'webapp'
laconic-so deployment --dir my-deployment port webapp 80

# Output example: 0.0.0.0:32768
```

To configure fixed ports, edit the spec file before creating the deployment:

```yaml
network:
  ports:
    webapp:
      - '8080:80'  # Maps host port 8080 to container port 80
    api:
      - '3000:3000'
```

Then create the deployment:

```bash
laconic-so --stack my-stack deploy create \
  --spec-file spec.yml \
  --deployment-dir my-deployment
```

### Volume Persistence

Volumes are preserved between stop/start cycles by default:

```bash
# Stop but keep data
laconic-so deployment --dir my-deployment stop

# Start again - data is still there
laconic-so deployment --dir my-deployment start
```

To completely remove all data:

```bash
# Stop and delete all volumes
laconic-so deployment --dir my-deployment stop --delete-volumes
```

Volume data is stored in `<deployment-dir>/data/`.

## Common Operations

### Viewing Logs

```bash
# All services, continuous follow
laconic-so deployment --dir my-deployment logs --follow

# Last 100 lines from all services
laconic-so deployment --dir my-deployment logs --tail 100

# Specific service only
laconic-so deployment --dir my-deployment logs webapp

# Combine options
laconic-so deployment --dir my-deployment logs --tail 50 --follow webapp
```

### Executing Commands in Containers

```bash
# Execute a command in a running service
laconic-so deployment --dir my-deployment exec webapp ls -la

# Interactive shell
laconic-so deployment --dir my-deployment exec webapp /bin/bash

# Run command with specific environment variables
laconic-so deployment --dir my-deployment exec webapp env VAR=value command
```

### Checking Service Status

```bash
# List all running services
laconic-so deployment --dir my-deployment ps

# Check using Docker directly
docker ps
```

### Updating a Running Deployment

If you need to change configuration after deployment:

```bash
# 1. Edit the spec file
vim my-deployment/spec.yml

# 2. Regenerate configuration
laconic-so deployment --dir my-deployment update

# 3. Restart services to apply changes
laconic-so deployment --dir my-deployment stop
laconic-so deployment --dir my-deployment start
```

## Multi-Service Deployments

Many stacks deploy multiple services that work together:

```bash
# Deploy a stack with multiple services
laconic-so --stack laconicd-with-console deploy init --output spec.yml
laconic-so --stack laconicd-with-console deploy create \
  --spec-file spec.yml \
  --deployment-dir laconicd-deployment

laconic-so deployment --dir laconicd-deployment start

# View all services
laconic-so deployment --dir laconicd-deployment ps

# View logs from specific services
laconic-so deployment --dir laconicd-deployment logs laconicd
laconic-so deployment --dir laconicd-deployment logs console
```

## ConfigMaps

ConfigMaps allow you to mount configuration files into containers:

```bash
# 1. Create the config directory in your deployment
mkdir -p my-deployment/data/my-config
echo "database_url=postgres://localhost" > my-deployment/data/my-config/app.conf

# 2. Reference in spec file
vim my-deployment/spec.yml
```

Add to spec.yml:
```yaml
configmaps:
  my-config: ./data/my-config
```

```bash
# 3. Restart to apply
laconic-so deployment --dir my-deployment stop
laconic-so deployment --dir my-deployment start
```

The files will be mounted in the container at `/config/` (or as specified by the stack).

## Deployment Directory Structure

A typical deployment directory contains:

```
my-deployment/
├── compose/
│   └── docker-compose-*.yml    # Generated compose files
├── config.env                   # Environment variables
├── deployment.yml              # Deployment metadata
├── spec.yml                    # Deployment specification
└── data/                       # Volume mounts and configs
    ├── service-data/           # Persistent service data
    └── config-maps/            # ConfigMap files
```

## Troubleshooting

### Common Issues

**Problem: "Cannot connect to Docker daemon"**

```bash
# Ensure Docker is running
docker ps

# Start Docker if needed (macOS)
open -a Docker

# Start Docker (Linux)
sudo systemctl start docker
```

**Problem: "Port already in use"**

```bash
# Either stop the conflicting service or use different ports
# Edit spec.yml before creating deployment:

network:
  ports:
    webapp:
      - '8081:80'  # Use 8081 instead of 8080
```

**Problem: "Image not found"**

```bash
# Build containers first
laconic-so --stack your-stack build-containers
```

**Problem: Volumes not persisting**

```bash
# Check if you used --delete-volumes when stopping
# Volume data is in: <deployment-dir>/data/

# Don't use --delete-volumes if you want to keep data:
laconic-so deployment --dir my-deployment stop

# Only use --delete-volumes when you want to reset completely:
laconic-so deployment --dir my-deployment stop --delete-volumes
```

**Problem: Services not starting**

```bash
# Check logs for errors
laconic-so deployment --dir my-deployment logs

# Check Docker container status
docker ps -a

# Try stopping and starting again
laconic-so deployment --dir my-deployment stop
laconic-so deployment --dir my-deployment start
```

### Inspecting Deployment State

```bash
# Check deployment directory structure
ls -la my-deployment/

# Check running containers
docker ps

# Check container details
docker inspect <container-name>

# Check networks
docker network ls

# Check volumes
docker volume ls
```

## CLI Commands Reference

### Stack Operations

```bash
# Clone required repositories
laconic-so --stack <name> setup-repositories

# Build container images
laconic-so --stack <name> build-containers
```

### Deployment Initialization

```bash
# Initialize deployment spec with defaults
laconic-so --stack <name> deploy init --output <spec-file>

# Initialize with configuration
laconic-so --stack <name> deploy init --output <spec-file> \
  --config PARAM1=value1,PARAM2=value2
```

### Deployment Creation

```bash
# Create deployment directory from spec
laconic-so --stack <name> deploy create \
  --spec-file <spec-file> \
  --deployment-dir <dir>
```

### Deployment Management

```bash
# Start all services
laconic-so deployment --dir <dir> start

# Stop services (preserves volumes)
laconic-so deployment --dir <dir> stop

# Stop and remove volumes
laconic-so deployment --dir <dir> stop --delete-volumes

# List running services
laconic-so deployment --dir <dir> ps

# View logs
laconic-so deployment --dir <dir> logs [--tail N] [--follow] [service]

# Show mapped port
laconic-so deployment --dir <dir> port <service> <private-port>

# Execute command in service
laconic-so deployment --dir <dir> exec <service> <command>

# Update configuration
laconic-so deployment --dir <dir> update
```

### Quick Deploy Commands

```bash
# Start stack directly
laconic-so --stack <name> deploy up

# Stop stack
laconic-so --stack <name> deploy down [--delete-volumes]

# View logs
laconic-so --stack <name> deploy logs

# Show port mapping
laconic-so --stack <name> deploy port <service> <port>
```

## Related Documentation

- [CLI Reference](./cli.md) - Complete CLI command documentation
- [Adding a New Stack](./adding-a-new-stack.md) - Creating custom stacks
- [Specification](./spec.md) - Internal structure and design
- [Kubernetes Enhancements](./k8s-deployment-enhancements.md) - Advanced K8s deployment options
- [Web App Deployment](./webapp.md) - Deploying web applications

## Examples

For more examples, see the test scripts:
- `scripts/quick-deploy-test.sh` - Quick deployment example
- `tests/deploy/run-deploy-test.sh` - Comprehensive test showing all features

## Summary

- Docker Compose is the default and recommended deployment mode
- Two workflows: deployment directory (recommended) or quick deploy
- The standard workflow is: setup → build → init → create → start
- Configuration is flexible with multiple override layers
- Volume persistence is automatic unless explicitly deleted
- All deployment state is contained in the deployment directory
- For Kubernetes deployments, see separate K8s documentation

You're now ready to deploy stacks using stack-orchestrator with Docker Compose!
