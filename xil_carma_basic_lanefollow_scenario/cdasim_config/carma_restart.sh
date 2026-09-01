#!/usr/bin/env bash

# ============================================================
# CARMA Test Runner
#
# Usage:
#   ./carma_test.sh 5
#
# If no number is provided, defaults to 1 run.
# ============================================================

set -u

# -------------------------
# Configuration
# -------------------------

WAIT_SECONDS=60
DEFAULT_RUN_COUNT=1

# -------------------------
# Get run count
# -------------------------

if [[ $# -ge 1 ]]; then
    RUN_COUNT="$1"
else
    RUN_COUNT="$DEFAULT_RUN_COUNT"
fi

# Make sure RUN_COUNT is a positive integer
if ! [[ "$RUN_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "ERROR: Number of runs must be a positive integer."
    echo
    echo "Usage:"
    echo "  $0 <number_of_runs>"
    echo
    echo "Example:"
    echo "  $0 10"
    exit 1
fi

# -------------------------
# CARLA cleanup
# -------------------------

cleanup_carla() {
    echo "Cleaning up carma_1 actors..."

    python3 - <<'PY'
import carla
import sys

try:
    client = carla.Client("localhost", 2000)
    client.set_timeout(5.0)

    world = client.get_world()
    actors = world.get_actors()

    targets = [
        actor
        for actor in actors
        if actor.attributes.get("role_name", "") == "carma_1"
    ]

    if targets:
        print(f"Found {len(targets)} carma_1 actor(s).")

        for actor in targets:
            print(f"Destroying {actor.type_id} (ID: {actor.id})")
            actor.destroy()

        print("Cleanup complete.")
    else:
        print("No carma_1 actors found.")

except Exception as e:
    print(f"CARLA cleanup failed: {e}")
    sys.exit(1)
PY
}

# -------------------------
# Start CARMA silently
# -------------------------

start_carma() {
    echo "Starting CARMA..."

    # Redirect stdout and stderr so Docker/CARMA
    # output does not appear in the terminal.
    carma start all >/dev/null 2>&1

    if [[ $? -ne 0 ]]; then
        echo "ERROR: carma start all failed."
        return 1
    fi

    echo "CARMA started."
}

# -------------------------
# Stop CARMA silently
# -------------------------

stop_carma() {
    echo "Stopping CARMA..."

    # Redirect stdout and stderr so Docker/CARMA
    # output does not appear in the terminal.
    carma stop all >/dev/null 2>&1

    if [[ $? -ne 0 ]]; then
        echo "ERROR: carma stop all failed."
        return 1
    fi

    echo "CARMA stopped."
}

# -------------------------
# Main
# -------------------------

completed_runs=0

echo
echo "=========================================="
echo "        CARMA AUTOMATED TEST RUNNER"
echo "=========================================="
echo "Requested runs : $RUN_COUNT"
echo "Wait time      : ${WAIT_SECONDS}s"
echo "=========================================="
echo

for ((run=1; run<=RUN_COUNT; run++)); do

    echo "------------------------------------------"
    echo "Run $run / $RUN_COUNT"
    echo "------------------------------------------"

    # Remove any old carma_1 actor BEFORE starting
    # the next CARMA instance.
    if ! cleanup_carla; then
        echo "ERROR: CARLA cleanup failed."
        echo "Aborting test."
        exit 1
    fi

    # Start CARMA
    if ! start_carma; then
        echo "ERROR: Failed to start CARMA."
        echo "Aborting test."
        exit 1
    fi

    echo "Waiting ${WAIT_SECONDS} seconds..."
    sleep "$WAIT_SECONDS"

    # Stop CARMA
    if ! stop_carma; then
        echo "ERROR: Failed to stop CARMA."
        echo "Aborting test."
        exit 1
    fi

    completed_runs=$((completed_runs + 1))

    echo
    echo "Run $run complete."
    echo "Progress: $completed_runs / $RUN_COUNT"
    echo

done

echo "=========================================="
echo "          CARMA TEST COMPLETE"
echo "=========================================="
echo "Runs requested : $RUN_COUNT"
echo "Runs completed : $completed_runs"
echo "=========================================="
