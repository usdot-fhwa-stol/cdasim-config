#!/usr/bin/env bash

# ============================================================
# CARMA Automated Test Runner
#
# Usage:
#   ./carma_restart.sh 50
#
# ============================================================

set -u

# -------------------------
# Configuration
# -------------------------

WAIT_SECONDS=60
STARTUP_WAIT_SECONDS=10
DEFAULT_RUN_COUNT=50

LOG_DIR="./carma_test_logs"

mkdir -p "$LOG_DIR"

# -------------------------
# Get number of runs
# -------------------------

if [[ $# -ge 1 ]]; then
    RUN_COUNT="$1"
else
    RUN_COUNT="$DEFAULT_RUN_COUNT"
fi

if ! [[ "$RUN_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "ERROR: Number of runs must be a positive integer."
    echo
    echo "Usage:"
    echo "  $0 <number_of_runs>"
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
# Start CARMA
# -------------------------

start_carma() {
    local log_file="$LOG_DIR/run_${CURRENT_RUN}_start.log"

    echo "Starting CARMA..."
    echo "CARMA output -> $log_file"

    # Run CARMA in the background.
    # Output goes to a log instead of the terminal.
    carma start all >"$log_file" 2>&1 &

    CARMA_PID=$!

    echo "CARMA start process: PID $CARMA_PID"

    # Give CARMA a chance to start.
    echo "Waiting ${STARTUP_WAIT_SECONDS}s for CARMA startup..."
    sleep "$STARTUP_WAIT_SECONDS"

    # Check whether the carma command itself died.
    if ! kill -0 "$CARMA_PID" 2>/dev/null; then
        echo "ERROR: carma start all exited unexpectedly."
        echo
        echo "Last 20 lines of CARMA startup log:"
        tail -20 "$log_file"
        return 1
    fi

    echo "CARMA startup process is running."
}

# -------------------------
# Stop CARMA
# -------------------------

stop_carma() {
    local log_file="$LOG_DIR/run_${CURRENT_RUN}_stop.log"

    echo "Stopping CARMA..."

    carma stop all >"$log_file" 2>&1

    local result=$?

    if [[ $result -ne 0 ]]; then
        echo "WARNING: carma stop all returned exit code $result"
        echo "See: $log_file"
    else
        echo "CARMA stopped."
    fi

    # If carma start all left a process running,
    # wait briefly for it to exit.
    if [[ -n "${CARMA_PID:-}" ]]; then
        if kill -0 "$CARMA_PID" 2>/dev/null; then
            echo "Waiting for CARMA start process to exit..."

            for ((i=1; i<=10; i++)); do
                if ! kill -0 "$CARMA_PID" 2>/dev/null; then
                    break
                fi

                sleep 1
            done
        fi
    fi

    return 0
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
echo "Startup wait   : ${STARTUP_WAIT_SECONDS}s"
echo "Logs           : $LOG_DIR"
echo "=========================================="
echo

for ((run=1; run<=RUN_COUNT; run++)); do

    CURRENT_RUN="$run"

    echo "------------------------------------------"
    echo "Run $run / $RUN_COUNT"
    echo "------------------------------------------"

    # Reset PID
    CARMA_PID=""

    # -------------------------
    # Cleanup
    # -------------------------

    if ! cleanup_carla; then
        echo "ERROR: CARLA cleanup failed."
        echo "Aborting."
        exit 1
    fi

    # -------------------------
    # Start CARMA
    # -------------------------

    if ! start_carma; then
        echo "ERROR: Failed to start CARMA."
        echo "Aborting."
        exit 1
    fi

    # -------------------------
    # Run test
    # -------------------------

    echo "CARMA is running."
    echo "Waiting ${WAIT_SECONDS}s..."

    sleep "$WAIT_SECONDS"

    # -------------------------
    # Stop CARMA
    # -------------------------

    stop_carma

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
echo
echo "Logs saved in:"
echo "  $LOG_DIR"
