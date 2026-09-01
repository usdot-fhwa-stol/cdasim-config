#!/usr/bin/env bash

set -e

# =========================
# Configuration
# =========================

RUN_COUNT=5
WAIT_SECONDS=35

# =========================
# Functions
# =========================

cleanup_carla() {
    echo "=== Cleaning up existing carma_1 actors ==="

    python3 - <<'PY'
import carla
import sys

try:
    client = carla.Client("localhost", 2000)
    client.set_timeout(5.0)

    world = client.get_world()
    actors = world.get_actors()

    targets = [
        actor for actor in actors
        if actor.attributes.get("role_name", "") == "carma_1"
    ]

    if targets:
        print(f"Found {len(targets)} carma_1 actor(s). Destroying...")

        for actor in targets:
            print(f"Destroying {actor.type_id} ({actor.id})")
            actor.destroy()
    else:
        print("No existing carma_1 actors found.")

except Exception as e:
    print(f"Could not clean up CARLA actors: {e}")
    sys.exit(1)
PY
}

# =========================
# Main loop
# =========================

completed_runs=0

echo "========================================"
echo "CARMA Test Runner"
echo "Runs requested: $RUN_COUNT"
echo "Wait time: ${WAIT_SECONDS}s"
echo "========================================"

for ((run=1; run<=RUN_COUNT; run++)); do

    echo
    echo "========================================"
    echo "Starting run $run / $RUN_COUNT"
    echo "========================================"

    cleanup_carla

    echo
    echo "=== Starting CARMA ==="
    carma start all

    echo
    echo "=== CARMA started ==="
    echo "Waiting ${WAIT_SECONDS} seconds..."

    sleep "$WAIT_SECONDS"

    echo
    echo "=== Stopping CARMA ==="
    carma stop all

    completed_runs=$((completed_runs + 1))

    echo
    echo "=== Run $run completed ==="
    echo "Completed: $completed_runs / $RUN_COUNT"

done

echo
echo "========================================"
echo "CARMA TEST COMPLETE"
echo "========================================"
echo "Runs completed: $completed_runs"
echo "Runs requested: $RUN_COUNT"
echo "========================================"
