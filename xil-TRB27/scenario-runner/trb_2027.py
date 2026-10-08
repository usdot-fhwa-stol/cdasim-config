#!/usr/bin/env python3
# Copyright 2026 Leidos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Spawns a static fire truck prop in Town10 for the TRB2027 Cooperative
Perception demo.

Connects to CARLA directly, spawns the fire truck once, and stays alive --
no scenario lifecycle to manage.
"""

import time

import carla

CARLA_HOST = "localhost"
CARLA_PORT = 2000
CONNECT_RETRY_INTERVAL_SECONDS = 2.0
CONNECT_TIMEOUT_SECONDS = 10.0

# After a map (re)load, the level needs a moment to finish streaming in
# before actors can be spawned -- spawning too soon reliably throws CARLA's
# generic "RuntimeError: std::exception" from spawn_actor().
MAP_LOAD_SETTLE_SECONDS = 5.0
SPAWN_RETRY_INTERVAL_SECONDS = 2.0
SPAWN_RETRY_ATTEMPTS = 10

TOWN_NAME = "Town10HD_Opt"
FIRE_TRUCK_BLUEPRINT = "vehicle.firetruck.actors"
FIRE_TRUCK_ROLE_NAME = "fire_truck"

# Coordinates obtained by manually driving to the yellow dot location in
# Town10 and reading off the CARLA transform.
FIRE_TRUCK_LOCATION = carla.Location(x=110.10, y=47.32, z=0.2)
FIRE_TRUCK_ROTATION = carla.Rotation(yaw=270.0)


def connect_to_carla() -> carla.Client:
    """
    Connect to the CARLA server, retrying until it's actually ready rather
    than failing immediately. This script can start running before the
    rest of the simulation stack (cdasim, CARLA itself) has finished
    coming up.
    """
    while True:
        try:
            client = carla.Client(CARLA_HOST, CARLA_PORT)
            client.set_timeout(CONNECT_TIMEOUT_SECONDS)
            client.get_world()
            return client
        except RuntimeError as exc:
            print(f"Waiting for CARLA server ({exc}), retrying...")
            time.sleep(CONNECT_RETRY_INTERVAL_SECONDS)


def spawn_fire_truck(world: carla.World) -> carla.Actor:
    """
    Spawn the fire truck, retrying on failure. A freshly loaded/streamed
    level can reject spawn_actor() calls for a few seconds with a generic
    RuntimeError even once the world object itself is reachable, so this
    retries rather than treating the first failure as fatal.
    """
    blueprint_library = world.get_blueprint_library()
    fire_truck_bp = blueprint_library.find(FIRE_TRUCK_BLUEPRINT)
    fire_truck_bp.set_attribute("role_name", FIRE_TRUCK_ROLE_NAME)
    spawn_transform = carla.Transform(FIRE_TRUCK_LOCATION, FIRE_TRUCK_ROTATION)

    for attempt in range(1, SPAWN_RETRY_ATTEMPTS + 1):
        try:
            return world.spawn_actor(fire_truck_bp, spawn_transform)
        except RuntimeError as exc:
            print(
                f"spawn_actor failed (attempt {attempt}/{SPAWN_RETRY_ATTEMPTS}): "
                f"{exc}, retrying..."
            )
            time.sleep(SPAWN_RETRY_INTERVAL_SECONDS)

    raise RuntimeError(
        f"Failed to spawn fire truck after {SPAWN_RETRY_ATTEMPTS} attempts"
    )


def main() -> None:
    client = connect_to_carla()
    world = client.get_world()

    if TOWN_NAME not in world.get_map().name:
        print(f"Switching server map to {TOWN_NAME}...")
        world = client.load_world(TOWN_NAME)
        print(f"Waiting {MAP_LOAD_SETTLE_SECONDS}s for the level to settle...")
        time.sleep(MAP_LOAD_SETTLE_SECONDS)

    fire_truck = spawn_fire_truck(world)

    # Static prop -- no physics simulation, so it can't be knocked over,
    # fall through the ground, or otherwise drift from its placed position.
    fire_truck.set_simulate_physics(False)

    print(
        f"Fire truck (id={fire_truck.id}) spawned and held static at "
        f"{FIRE_TRUCK_LOCATION}."
    )

    # Nothing else to do -- the fire truck has no behavior. Stay alive so
    # the process (and the actor it owns) persists. Lifecycle across demo
    # loop iterations is controlled externally by restarting this
    # container, not by any timeout here.
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        fire_truck.destroy()


if __name__ == "__main__":
    main()
