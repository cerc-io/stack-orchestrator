# ZFS Setup for Biscayne

## Current State

```
biscayne                      none          (pool root)
biscayne/DATA                 none
biscayne/DATA/home            /home         42G
biscayne/DATA/home/solana     /home/solana  2.9G
biscayne/DATA/srv             /srv          712G
biscayne/DATA/srv/backups     /srv/backups  208G
biscayne/DATA/volumes/solana  (zvol, 4T)    → block-mounted at /srv/solana
```

Docker root: `/var/lib/docker` on root filesystem (`/dev/md0`, 439G).

## Target State

```
biscayne/DATA/deployments     /srv/deployments   ← laconic-so deployment dirs (snapshotted)
biscayne/DATA/var/docker      /var/lib/docker    ← docker storage on ZFS
biscayne/DATA/volumes/solana  (zvol, 4T)         ← bulk solana data (not backed up)
```

## Steps

### 1. Create deployments dataset

```bash
zfs create -o mountpoint=/srv/deployments biscayne/DATA/deployments
```

### 2. Move docker onto ZFS

Stop docker and all containers first:

```bash
systemctl stop docker.socket docker.service
```

Create the dataset:

```bash
zfs create -o mountpoint=/var/lib/docker biscayne/DATA/var
zfs create biscayne/DATA/var/docker
```

Copy existing docker data (if any worth keeping):

```bash
rsync -aHAX /var/lib/docker.bak/ /var/lib/docker/
```

Or just start fresh — the only running containers are telegraf/influxdb monitoring
which can be recreated.

Start docker:

```bash
systemctl start docker.service
```

### 3. Grant ZFS permissions to the backup user

```bash
zfs allow -u <backup-user> destroy,snapshot,send,hold,release,mount biscayne/DATA/deployments
```

### 4. Create remote receiving datasets

On mysterio:

```bash
zfs create -p edith/DATA/backlog/biscayne-main
```

On ardham:

```bash
zfs create -p batterywharf/DATA/backlog/biscayne-main
```

These will fail until SSH keys and network access are configured for biscayne
to reach these hosts. The backup script handles this gracefully.

### 5. Install backlog.sh and crontab

```bash
mkdir -p ~/.local/bin
cp scripts/backlog.sh ~/.local/bin/backlog.sh
chmod +x ~/.local/bin/backlog.sh
crontab -e
# Add: 01 0 * * * /home/<user>/.local/bin/backlog.sh
```

## Volume Layout

laconic-so deployment at `/srv/deployments/agave/`:

| Volume | Location | Backed up |
|---|---|---|
| validator-config | `/srv/deployments/agave/data/validator-config/` | Yes (ZFS snapshot) |
| doublezero-config | `/srv/deployments/agave/data/doublezero-config/` | Yes (ZFS snapshot) |
| validator-ledger | `/srv/solana/ledger/` (zvol) | No (rebuildable) |
| validator-accounts | `/srv/solana/accounts/` (zvol) | No (rebuildable) |
| validator-snapshots | `/srv/solana/snapshots/` (zvol) | No (rebuildable) |

The laconic-so spec.yml must map the heavy volumes to zvol paths and the small
config volumes to the deployment directory.
