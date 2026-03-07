#!/bin/bash
# Run a command in a tmux pane and capture its output.
# User sees it streaming in the pane; caller gets stdout back.
#
# Usage: pane-exec.sh <pane-id> <command...>
# Example: pane-exec.sh %6565 ansible-playbook -i inventory/switches.yml playbooks/foo.yml

set -euo pipefail

PANE="$1"
shift
CMD="$*"

TMPFILE=$(mktemp /tmp/pane-output.XXXXXX)
MARKER="__PANE_EXEC_DONE_${RANDOM}_$$__"

cleanup() {
    tmux pipe-pane -t "$PANE" 2>/dev/null || true
    rm -f "$TMPFILE"
}
trap cleanup EXIT

# Start capturing pane output
tmux pipe-pane -o -t "$PANE" "cat >> $TMPFILE"

# Send the command, then echo a marker so we know when it's done
tmux send-keys -t "$PANE" "$CMD; echo $MARKER" Enter

# Wait for the marker
while ! grep -q "$MARKER" "$TMPFILE" 2>/dev/null; do
    sleep 0.5
done

# Stop capturing
tmux pipe-pane -t "$PANE"

# Strip ANSI escape codes, remove the marker line, output the rest
sed 's/\x1b\[[0-9;]*[a-zA-Z]//g; s/\x1b\[[?][0-9]*[a-zA-Z]//g' "$TMPFILE" | grep -v "$MARKER"
