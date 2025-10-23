#!/usr/bin/env bash
# Freqtrade Stop Script for Indian Brokers

set -e

echo "Stopping Freqtrade..."

# Find and kill freqtrade processes
PIDS=$(pgrep -f "freqtrade trade" || true)

if [ -z "$PIDS" ]; then
    echo "No running Freqtrade processes found"
    exit 0
fi

echo "Found Freqtrade processes: $PIDS"
echo "Sending SIGTERM..."

for PID in $PIDS; do
    kill -TERM $PID 2>/dev/null || true
done

# Wait for graceful shutdown
sleep 3

# Check if still running
REMAINING=$(pgrep -f "freqtrade trade" || true)
if [ -n "$REMAINING" ]; then
    echo "Processes still running, sending SIGKILL..."
    for PID in $REMAINING; do
        kill -KILL $PID 2>/dev/null || true
    done
fi

echo "Freqtrade stopped"
