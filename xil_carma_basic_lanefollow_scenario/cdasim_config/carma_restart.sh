#!/usr/bin/env bash

# ============================================================
# CARLA + CARMA Automated Test Runner
#
# Usage:
#   ./carma_restart.sh
#   ./carma_restart.sh 10
#   ./carma_restart.sh 50
#
# Default:
#   50 runs
#
# Each CARMA run lasts 60 seconds.
# ============================================================

set -u

# ============================================================
# Configuration
# ============================================================

DEFAULT_RUN_COUNT=50

CARLA_DIR="/home/simpc2/CARLA/Carla-0.10.0-Linux-Shipping"
CARLA_SCRIPT="$CARLA_DIR/CarlaUnreal.sh"

CARLA_HOST="localhost"
CARLA_PORT=2000

CARLA_STARTUP_WAIT=10
CARLA_CHECK_INTERVAL=2

CARMA_RUN_SECONDS=60

LOG_DIR="$HOME/carma_test_logs"

# ============================================================
# Runtime variables
# ============================================================

CARLA_PID=""
CARMA_PID=""

mkdir -p "$LOG_DIR"

# ============================================================
# Number of runs
# ============================================================

if [[ $# -ge 1 ]]; then
    RUN_COUNT="$1"
else
    RUN_COUNT="$DEFAULT_RUN_COUNT"
fi

if ! [[ "$RUN_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "ERROR: Number of runs must be a positive integer."
    echo
    echo "Usage:"
    echo "  $0 [number_of_runs]"
    echo
    echo "Examples:"
    echo "  $0"
    echo "  $0 10"
    echo "  $0 50"
    exit 1
fi

# ============================================================
# Check whether CARLA is accepting connections
# ============================================================

carla_is_ready() {
    python3 - <<'PY' >/dev/null 2>&1
import carla

try:
    client = carla.Client("localhost", 2000)
    client.set_timeout(2.0)

    # Actually communicate with CARLA.
    client.get_world()

    sys_exit = 0
except Exception:
    sys_exit = 1

raise SystemExit(sys_exit)
PY
}

# ============================================================
# Check whether CARLA process exists
# ============================================================

carla_process_running() {
    if [[ -n "${CARLA_PID:-}" ]]; then
        kill -0 "$CARLA_PID" 2>/dev/null
        return $?
    fi

    # Fallback in case the script was restarted while CARLA
    # was already running.
    pgrep -f "$CARLA_SCRIPT" >/dev/null 2>&1
}

# ============================================================
# Start CARLA
# ============================================================

start_carla() {

    echo "Starting CARLA..."

    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")

    local log_file="$LOG_DIR/carla_${timestamp}.log"

    echo "CARLA log: $log_file"

    (
        cd "$CARLA_DIR" || exit 1

        "$CARLA_SCRIPT" >"$log_file" 2>&1
    ) &

    CARLA_PID=$!

    echo "CARLA PID: $CARLA_PID"

    echo "Waiting for CARLA to become ready..."

    local elapsed=0

    while true; do

        # Check whether the process crashed/exited.
        if ! kill -0 "$CARLA_PID" 2>/dev/null; then

            echo
            echo "ERROR: CARLA exited before becoming ready."
            echo
            echo "Last 30 lines of CARLA log:"
            tail -30 "$log_file"
            echo

            return 1
        fi

        # Actually try connecting to CARLA.
        if carla_is_ready; then
            echo "CARLA is ready."
            return 0
        fi

        sleep "$CARLA_CHECK_INTERVAL"

        elapsed=$((elapsed + CARLA_CHECK_INTERVAL))

        # No hard timeout here; CARLA can take a while to load.
        # Print progress every 10 seconds.
        if (( elapsed % 10 == 0 )); then
            echo "Still waiting for CARLA... ${elapsed}s"
        fi
    done
}

# ============================================================
# Ensure CARLA is running
# ============================================================

ensure_carla() {

    echo "Checking CARLA..."

    if carla_is_ready; then
        echo "CARLA is already ready."
        return 0
    fi

    echo "CARLA is not responding."

    start_carla
}

# ============================================================
# Cleanup carma_1 actors
# ============================================================

cleanup_carla_actors() {

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
            try:
                print(
                    f"Destroying {actor.type_id} "
                    f"(ID: {actor.id})"
                )
                actor.destroy()
            except Exception as e:
                print(
                    f"Failed to destroy actor {actor.id}: {e}"
                )

        print("Cleanup complete.")

    else:
        print("No carma_1 actors found.")

except Exception as e:
    print(f"CARLA cleanup failed: {e}")
    sys.exit(1)
PY
}

# ============================================================
# Start CARMA
# ============================================================

start_carma() {

    local log_file="$LOG_DIR/run_${CURRENT_RUN}_carma_start.log"

    echo "Starting CARMA..."
    echo "CARMA log: $log_file"

    # Start CARMA in the background.
    #
    # Output is captured instead of printed to the terminal.
    carma start all >"$log_file" 2>&1 &

    CARMA_PID=$!

    echo "CARMA process PID: $CARMA_PID"

    # Give CARMA time to initialize.
    echo "Waiting for CARMA startup..."

    sleep 10

    # Check whether the command died immediately.
    if ! kill -0 "$CARMA_PID" 2>/dev/null; then
        echo "WARNING: carma start all exited."

        echo "Last 20 lines of CARMA log:"
        tail -20 "$log_file"

        return 1
    fi

    echo "CARMA started."
}

# ============================================================
# Stop CARMA
# ============================================================

stop_carma() {

    local log_file="$LOG_DIR/run_${CURRENT_RUN}_carma_stop.log"

    echo "Stopping CARMA..."

    carma stop all >"$log_file" 2>&1

    local result=$?

    if [[ $result -ne 0 ]]; then
        echo "WARNING: carma stop all returned $result"
        echo "See: $log_file"
    else
        echo "CARMA stopped."
    fi

    # Give Docker/CARMA a moment to finish shutting down.
    sleep 3

    CARMA_PID=""

    return 0
}

# ============================================================
# Verify CARLA after CARMA operation
# ============================================================

verify_carla() {

    echo "Checking CARLA after CARMA run..."

    if carla_is_ready; then
        echo "CARLA is healthy."
        return 0
    fi

    echo
    echo "=========================================="
    echo "CARLA IS NOT RESPONDING"
    echo "=========================================="
    echo

    return 1
}

# ============================================================
# Handle CARLA crash
# ============================================================

restart_carla() {

    echo
    echo "=========================================="
    echo "RESTARTING CARLA"
    echo "=========================================="

    # If our tracked process still exists, terminate it.
    if [[ -n "${CARLA_PID:-}" ]]; then

        if kill -0 "$CARLA_PID" 2>/dev/null; then
            echo "Terminating old CARLA process..."

            kill "$CARLA_PID" 2>/dev/null || true

            sleep 3

            if kill -0 "$CARLA_PID" 2>/dev/null; then
                echo "CARLA did not terminate. Sending SIGKILL..."
                kill -9 "$CARLA_PID" 2>/dev/null || true
            fi
        fi
    fi

    CARLA_PID=""

    # Make sure no stale CarlaUnreal process remains.
    pkill -f "$CARLA_SCRIPT" 2>/dev/null || true

    sleep 5

    # Start CARLA again.
    start_carla
}

# ============================================================
# Cleanup on Ctrl+C / script exit
# ============================================================

cleanup_on_exit() {

    echo
    echo "Script interrupted."

    echo "Stopping CARMA..."
    carma stop all >/dev/null 2>&1 || true

    exit 1
}

trap cleanup_on_exit INT TERM

# ============================================================
# Main
# ============================================================

completed_runs=0
failed_runs=0

echo
echo "=========================================="
echo "       CARLA + CARMA TEST RUNNER"
echo "=========================================="
echo "Requested runs : $RUN_COUNT"
echo "CARMA duration : ${CARMA_RUN_SECONDS}s"
echo "CARLA          : $CARLA_SCRIPT"
echo "Logs           : $LOG_DIR"
echo "=========================================="
echo

# ------------------------------------------------------------
# Make sure CARLA is running before run 1.
# ------------------------------------------------------------

if ! ensure_carla; then

    echo
    echo "ERROR: Could not start CARLA."
    exit 1

fi

echo

# ============================================================
# Test loop
# ============================================================

for ((run=1; run<=RUN_COUNT; run++)); do

    CURRENT_RUN="$run"

    echo
    echo "=========================================="
    echo "RUN $run / $RUN_COUNT"
    echo "=========================================="

    # --------------------------------------------------------
    # Make sure CARLA is available
    # --------------------------------------------------------

    if ! carla_is_ready; then

        echo "CARLA is not available."
        echo "Restarting CARLA before continuing..."

        if ! restart_carla; then
            echo "ERROR: CARLA restart failed."
            exit 1
        fi

    fi

    # --------------------------------------------------------
    # Remove previous carma_1 actor
    # --------------------------------------------------------

    if ! cleanup_carla_actors; then

        echo "WARNING: Actor cleanup failed."
        echo "Restarting CARLA..."

        if ! restart_carla; then
            echo "ERROR: CARLA restart failed."
            exit 1
        fi

        # Try cleanup once more.
        if ! cleanup_carla_actors; then
            echo "ERROR: Could not clean up CARLA."
            exit 1
        fi
    fi

    # --------------------------------------------------------
    # Start CARMA
    # --------------------------------------------------------

    if ! start_carma; then

        echo "ERROR: CARMA failed to start."
        failed_runs=$((failed_runs + 1))

        echo "Attempting CARMA shutdown..."
        carma stop all >/dev/null 2>&1 || true

        continue
    fi

    # --------------------------------------------------------
    # Let CARMA operate
    # --------------------------------------------------------

    echo
    echo "CARMA operating for ${CARMA_RUN_SECONDS} seconds..."

    for ((remaining=CARMA_RUN_SECONDS; remaining>0; remaining-=10)); do

        if (( remaining <= 10 )); then
            echo "  ${remaining}s remaining..."
            sleep "$remaining"
        else
            echo "  ${remaining}s remaining..."
            sleep 10
        fi

    done

    # --------------------------------------------------------
    # Stop CARMA
    # --------------------------------------------------------

    stop_carma

    # --------------------------------------------------------
    # Check CARLA
    # --------------------------------------------------------

    if ! verify_carla; then

        echo "CARLA appears to have crashed."

        if ! restart_carla; then
            echo "ERROR: Could not restart CARLA."
            exit 1
        fi

        echo "CARLA restarted successfully."
    fi

    # --------------------------------------------------------
    # Run completed
    # --------------------------------------------------------

    completed_runs=$((completed_runs + 1))

    echo
    echo "Run $run complete."
    echo "Completed : $completed_runs / $RUN_COUNT"
    echo "Failed    : $failed_runs"

done

# ============================================================
# Final summary
# ============================================================

echo
echo "=========================================="
echo "          TESTING COMPLETE"
echo "=========================================="
echo "Requested runs : $RUN_COUNT"
echo "Completed runs : $completed_runs"
echo "Failed runs    : $failed_runs"
echo "=========================================="
echo
echo "Logs:"
echo "  $LOG_DIR"
echo

Run it

Make sure it's executable:

chmod +x carma_restart.sh


Then simply:

./carma_restart.sh


That defaults to 50 runs.

Or:

./carma_restart.sh 10


for 10 runs.

What happens when CARLA crashes

For example, if CARLA crashes during run 4:

==========================================
RUN 4 / 50
==========================================
...
CARMA operating for 60 seconds...
...
Stopping CARMA...
CARMA stopped.
Checking CARLA after CARMA run...

==========================================
CARLA IS NOT RESPONDING
==========================================

CARLA appears to have crashed.

==========================================
RESTARTING CARLA
==========================================
Starting CARLA...
CARLA PID: 12345
Waiting for CARLA to become ready...
Still waiting for CARLA... 10s
CARLA is ready.
CARLA restarted successfully.

Run 4 complete.
Completed : 4 / 50


Then it proceeds to run 5 rather than stopping the entire test.

One other important point: because your CARLA is crashing with SIGSEGV (signal 11), this script can detect and recover from the crash, but it won't fix the underlying CARLA crash. The saved CARLA logs in ~/carma_test_logs/ should make it easier to correlate the crash with the preceding CARMA run.