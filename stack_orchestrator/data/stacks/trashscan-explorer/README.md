# TrashScan Explorer Stack

TrashScan is a blockchain explorer for Gorbagana mainnet (Solana fork).

## Quick Start

```bash
# 1. Setup repositories (clones TrashScan-Explorer to ~/cerc/)
laconic-so --stack trashscan-explorer setup-repositories

# 2. Build containers
laconic-so --stack trashscan-explorer build-containers

# 3. Deploy
laconic-so --stack trashscan-explorer deploy-system up

# 4. Verify
docker ps --filter "name=trashscan"
curl http://localhost:5001/

# 5. View logs
laconic-so --stack trashscan-explorer deploy-system logs -f

# 6. Stop
laconic-so --stack trashscan-explorer deploy-system down
```

## Access

After deployment, access the explorer at: **http://localhost:5001**

Note: Default port is 5001 to avoid conflict with macOS AirPlay Receiver on port 5000.

## Components

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| trashscan-explorer | cerc/trashscan-explorer:local | 5001 | React/Express blockchain explorer |
| trashscan-db | postgres:14-alpine | (internal) | PostgreSQL database |

## Configuration

Environment variables can be set in your deployment configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| NODE_ENV | production | Node environment |
| DATABASE_URL | postgres://trashscan:password@trashscan-db:5432/trashscan | Database connection string |
| TRASHSCAN_HOST_PORT | 5001 | Host port for explorer |
| SESSION_SECRET | change-me-in-production | Express session secret |
| RPC_URL | https://rpc.trashscan.io/ | Gorbagana RPC endpoint |
| RUN_MIGRATIONS | true | Run database migrations on startup |

## External Dependencies

The explorer connects to the Gorbagana RPC at https://rpc.trashscan.io/ by default.

## Files in This Stack

```
stack-orchestrator/stack_orchestrator/data/
├── stacks/trashscan-explorer/
│   ├── stack.yml                    # Stack definition
│   └── README.md                    # This file
├── container-build/cerc-trashscan-explorer/
│   ├── Dockerfile.base              # Multi-stage build (base)
│   ├── Dockerfile                   # Final image with scripts
│   ├── build.sh                     # Build script
│   └── scripts/
│       └── start-explorer.sh        # Container startup script
└── compose/
    └── docker-compose-trashscan-explorer.yml  # Docker Compose
```

## Verification Checklist

After deployment, verify:

- [ ] `docker ps` shows both containers as `(healthy)`
- [ ] `curl http://localhost:5001/` returns HTTP 200
- [ ] Logs show "TrashScan Explorer starting..." and "Database is available!"

## Troubleshooting

### Port 5000 conflict (macOS)
macOS AirPlay Receiver uses port 5000. This stack defaults to 5001.
To use a different port: `export TRASHSCAN_HOST_PORT=8080`

### Missing assets error during build
The upstream TrashScan-Explorer repo may be missing the `attached_assets/` directory.
Create placeholder images if needed:
```bash
cd ~/cerc/TrashScan-Explorer
mkdir -p attached_assets
# Create placeholder images for any missing assets
```

### "Cannot find package 'vite'" error
The Dockerfile.base includes vite in production deps to handle this.
