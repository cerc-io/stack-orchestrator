# Deploying to the Laconic Network

## Overview

The Laconic network uses a **registry-based deployment model** where everything is published as blockchain records.

## Key Documentation in stack-orchestrator

- `docs/laconicd-with-console.md` - Setting up a laconicd network
- `docs/webapp.md` - Webapp building/running
- `stack_orchestrator/deploy/webapp/` - Implementation (14 modules)

## Core Concepts

### LRN (Laconic Resource Name)
Format: `lrn://laconic/[namespace]/[name]`

Examples:
- `lrn://laconic/deployers/my-deployer-name`
- `lrn://laconic/dns/example.com`
- `lrn://laconic/deployments/example.com`

### Registry Record Types

| Record Type | Purpose |
|-------------|---------|
| `ApplicationRecord` | Published app metadata |
| `WebappDeployer` | Deployment service offering |
| `ApplicationDeploymentRequest` | User's request to deploy |
| `ApplicationDeploymentAuction` | Optional bidding for deployers |
| `ApplicationDeploymentRecord` | Completed deployment result |

## Deployment Workflows

### 1. Direct Deployment

```
User publishes ApplicationDeploymentRequest
    → targets specific WebappDeployer (by LRN)
    → includes payment TX hash
    → Deployer picks up request, builds, deploys, publishes result
```

### 2. Auction-Based Deployment

```
User publishes ApplicationDeploymentAuction
    → Deployers bid (commit/reveal phases)
    → Winner selected
    → User publishes request targeting winner
```

## Key CLI Commands

### Publish a Deployer Service
```bash
laconic-so publish-webapp-deployer --laconic-config config.yml \
  --api-url https://deployer-api.example.com \
  --name my-deployer \
  --payment-address laconic1... \
  --minimum-payment 1000alnt
```

### Request Deployment (User Side)
```bash
laconic-so request-webapp-deployment --laconic-config config.yml \
  --app lrn://laconic/apps/my-app \
  --deployer lrn://laconic/deployers/xyz \
  --make-payment auto
```

### Run Deployer Service (Deployer Side)
```bash
laconic-so deploy-webapp-from-registry --laconic-config config.yml --discover
```

## Laconic Config File

All tools require a laconic config file (`laconic.toml`):

```toml
[cosmos]
address_prefix = "laconic"
chain_id = "laconic_9000-1"
endpoint = "http://localhost:26657"
key = "<account-name>"
password = "<account-password>"
```

## Setting Up a Local Laconicd Network

```bash
# Clone and build
laconic-so --stack fixturenet-laconic-loaded setup-repositories
laconic-so --stack fixturenet-laconic-loaded build-containers
laconic-so --stack fixturenet-laconic-loaded deploy create
laconic-so deployment --dir laconic-loaded-deployment start

# Check status
laconic-so deployment --dir laconic-loaded-deployment exec cli "laconic registry status"
```

## Key Implementation Files

| File | Purpose |
|------|---------|
| `publish_webapp_deployer.py` | Register deployment service on network |
| `publish_deployment_auction.py` | Create auction for deployers to bid on |
| `handle_deployment_auction.py` | Monitor and bid on auctions (deployer-side) |
| `request_webapp_deployment.py` | Create deployment request (user-side) |
| `deploy_webapp_from_registry.py` | Process requests and deploy (deployer-side) |
| `request_webapp_undeployment.py` | Request app removal |
| `undeploy_webapp_from_registry.py` | Process removal requests |
| `util.py` | LaconicRegistryClient - all registry interactions |

## Payment System

- **Token Denom**: `alnt` (Laconic network tokens)
- **Payment Options**:
  - `--make-payment`: Create new payment with amount (or "auto" for deployer's minimum)
  - `--use-payment`: Reference existing payment TX

## What's NOT Well-Documented

1. No end-to-end tutorial for full deployment workflow
2. Stack publishing (vs webapp) process unclear
3. LRN naming conventions not formally specified
4. Payment economics and token mechanics
