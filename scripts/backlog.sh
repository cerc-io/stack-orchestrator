#!/bin/bash

set -Eeuo pipefail

export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
mkdir -p "$XDG_RUNTIME_DIR"

# optional suffix from command-line, prepend dash if non-empty
SUFFIX="${1:-}"
SUFFIX="${SUFFIX:+-$SUFFIX}"

# define variables
DATASET="biscayne/DATA/deployments"
DEPLOYMENT_DIR="/srv/deployments/agave"
LOG_FILE="$HOME/.backlog_history"
ZFS_HOLD="backlog:pending"
SERVICE_STOP_TIMEOUT="300"
SNAPSHOT_RETENTION="6"
SNAPSHOT_PREFIX="backlog"
SNAPSHOT_TAG="$(date +%Y%m%d)${SUFFIX}"
SNAPSHOT="${DATASET}@${SNAPSHOT_PREFIX}-${SNAPSHOT_TAG}"

# remote replication targets
REMOTES=(
    "mysterio:edith/DATA/backlog/biscayne-main"
    "ardham:batterywharf/DATA/backlog/biscayne-main"
)

# log functions
log() {
    local time_fmt
    time_fmt=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$time_fmt] $1" >> "$LOG_FILE"
}

log_close() {
    local end_time duration
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    log "Backlog completed in ${duration}s"
    echo "" >> "$LOG_FILE"
}

# service controls
services() {
    local action="$1"

    case "$action" in
        stop)
            log "Stopping agave deployment..."
            laconic-so deployment --dir "$DEPLOYMENT_DIR" stop

            log "Waiting for services to fully stop..."
            local deadline=$(( $(date +%s) + SERVICE_STOP_TIMEOUT ))
            while true; do
                local running
                running=$(docker ps --filter "label=com.docker.compose.project.working_dir=$DEPLOYMENT_DIR" -q 2>/dev/null | wc -l)
                if [[ "$running" -eq 0 ]]; then
                    break
                fi
                if (( $(date +%s) >= deadline )); then
                    log "WARNING: Timeout waiting for services to stop; continuing."
                    break
                fi
                sleep 0.2
            done
            ;;
        start)
            log "Starting agave deployment..."
            laconic-so deployment --dir "$DEPLOYMENT_DIR" start
            ;;
        *)
            log "ERROR: Unknown action '$action' in services()"
            exit 2
            ;;
    esac
}

# send a snapshot to one remote
# args: snap remote_host remote_dataset
snapshot_send_one() {
    local snap="$1" remote_host="$2" remote_dataset="$3"

    log "Checking remote snapshots on $remote_host..."

    local -a local_snaps remote_snaps
    mapfile -t local_snaps < <(zfs list -H -t snapshot -o name -s creation -d1 "$DATASET" | grep -F "${DATASET}@${SNAPSHOT_PREFIX}-")
    mapfile -t remote_snaps < <(ssh "$remote_host" zfs list -H -t snapshot -o name -s creation "$remote_dataset" | grep -F "${remote_dataset}@${SNAPSHOT_PREFIX}-" || true)

    # find latest common snapshot
    local base=""
    local local_snap remote_snap remote_check
    for local_snap in "${local_snaps[@]}"; do
        remote_snap="${local_snap/$DATASET/$remote_dataset}"
        for remote_check in "${remote_snaps[@]}"; do
            if [[ "$remote_check" == "$remote_snap" ]]; then
                base="$local_snap"
                break
            fi
        done
    done

    if [[ -z "$base" && ${#remote_snaps[@]} -eq 0 ]]; then
        log "No remote snapshots found on $remote_host — sending full snapshot."
        if zfs send "$snap" | ssh "$remote_host" zfs receive -sF "$remote_dataset"; then
            log "Full send to $remote_host succeeded."
            return 0
        else
            log "ERROR: Full send to $remote_host failed."
            return 1
        fi
    elif [[ -n "$base" ]]; then
        log "Common base snapshot $base found — sending incremental to $remote_host."
        if zfs send -i "$base" "$snap" | ssh "$remote_host" zfs receive -sF "$remote_dataset"; then
            log "Incremental send to $remote_host succeeded."
            return 0
        else
            log "ERROR: Incremental send to $remote_host failed."
            return 1
        fi
    else
        log "STALE DESTINATION: $remote_host has snapshots but no common base with local — skipping."
        return 1
    fi
}

# send snapshot to all remotes
snapshot_send() {
    local snap="$1"
    local failure_count=0

    set +e
    local entry remote_host remote_dataset
    for entry in "${REMOTES[@]}"; do
        remote_host="${entry%%:*}"
        remote_dataset="${entry#*:}"
        if ! snapshot_send_one "$snap" "$remote_host" "$remote_dataset"; then
            failure_count=$((failure_count + 1))
        fi
    done
    set -e

    if [[ "$failure_count" -gt 0 ]]; then
        log "WARNING: $failure_count destination(s) failed or are out of sync."
        return 1
    fi
    return 0
}

# snapshot management
snapshot() {
    local action="$1"

    case "$action" in
        create)
            log "Creating snapshot: $SNAPSHOT"
            zfs snapshot "$SNAPSHOT"
            zfs hold "$ZFS_HOLD" "$SNAPSHOT" || log "ERROR: Failed to hold $SNAPSHOT"
            ;;
        send)
            log "Sending snapshot $SNAPSHOT..."
            if snapshot_send "$SNAPSHOT"; then
                log "Snapshot send completed. Releasing hold."
                zfs release "$ZFS_HOLD" "$SNAPSHOT" || log "ERROR: Failed to release hold on $SNAPSHOT"
            else
                log "WARNING: Snapshot send encountered errors. Hold retained on $SNAPSHOT."
            fi
            ;;
        prune)
            if [[ "$SNAPSHOT_RETENTION" -gt 0 ]]; then
                log "Pruning old snapshots in $DATASET (retaining $SNAPSHOT_RETENTION destroyable snapshots)..."

                local -a all_snaps destroyable
                mapfile -t all_snaps < <(zfs list -H -t snapshot -o name -s creation -d1 "$DATASET" | grep -F "${DATASET}@${SNAPSHOT_PREFIX}-")

                destroyable=()
                for snap in "${all_snaps[@]}"; do
                    if zfs destroy -n -- "$snap" &>/dev/null; then
                        destroyable+=("$snap")
                    else
                        log "Skipping $snap — snapshot not destroyable (likely held)"
                    fi
                done

                local count to_destroy
                count="${#destroyable[@]}"
                to_destroy=$((count - SNAPSHOT_RETENTION))

                if [[ "$to_destroy" -le 0 ]]; then
                    log "Nothing to prune — only $count destroyable snapshots exist"
                else
                    local i
                    for (( i=0; i<to_destroy; i++ )); do
                        snap="${destroyable[$i]}"
                        log "Destroying snapshot: $snap"
                        if ! zfs destroy -- "$snap"; then
                            log "WARNING: Failed to destroy $snap despite earlier check"
                        fi
                    done
                fi
            else
                log "Skipping pruning — retention is set to $SNAPSHOT_RETENTION"
            fi
            ;;
        *)
            log "ERROR: Snapshot unknown action: $action"
            exit 2
            ;;
    esac
}

# open logging and begin execution
mkdir -p "$(dirname -- "$LOG_FILE")"

start_time=$(date +%s)
exec >> "$LOG_FILE" 2>&1
trap 'log_close' EXIT
trap 'rc=$?; log "ERROR: command failed at line $LINENO (exit $rc)"; exit $rc' ERR

log "Backlog Started"

if zfs list -H -t snapshot -o name -d1 "$DATASET" | grep -qxF "$SNAPSHOT"; then
    log "WARNING: Snapshot $SNAPSHOT already exists. Exiting."
    exit 1
fi

services stop
snapshot create
services start
snapshot send
snapshot prune

# end
