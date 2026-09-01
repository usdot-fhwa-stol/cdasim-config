#!/usr/bin/env bash

set -e

echo "=== Cleaning up existing carma_1 actors ==="

python3 - <<'PY'
import carla
import sys

try:
    client = carla.Client("localhost", 2000)
    client.set_timeout(5.0)

    world = client.get_world()
    actors = world.get_actors()

    targets = []

    for actor in actors:
        role_name = actor.attributes.get("role_name", "")

        if role_name == "carma_1":
            targets.append(actor)

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

echo
echo "=== Starting CARMA ==="
carma start all

echo
echo "=== CARMA started. Waiting 35 seconds ==="
sleep 35

echo
echo "=== Stopping CARMA ==="
carma stop all

echo
echo "=== Done ==="
