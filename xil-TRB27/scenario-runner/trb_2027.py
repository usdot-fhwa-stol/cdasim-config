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

Deliberately not built on ScenarioRunner's BasicScenario framework. That
machinery (behavior trees, timeouts, test criteria) is for actively-driven
scenario actors; for a static, physics-free prop with no behavior of its
own it was unnecessary complexity, and its timeout/Idle handling interacted
badly with this script potentially starting before the rest of the
simulation stack was ready, causing the fire truck to be torn down shortly
after spawning. This connects to CARLA directly, spawns the fire truck
once, and stays alive -- no scenario lifecycle to manage.
"""

import time

import carla

CARLA_HOST = "localhost"
CARLA_PORT = 2000
CONNECT_RETRY_INTERVAL_SECONDS = 2.0
CONNECT_TIMEOUT_SECONDS = 10.0

TOWN_NAME = "Town10HD_Opt"
FIRE_TRUCK_BLUEPRINT = "vehicle.firetruck.actors"
FIRE_TRUCK_ROLE_NAME = "fire_truck"

# Coordinates obtained by manually driving to the yellow dot location in
# Town10 and reading off the CARLA transform.
FIRE_TRUCK_LOCATION = carla.Location(x=110.10, y=47.32, z=0.03)
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


def main() -> None:
    client = connect_to_carla()
    world = client.get_world()

    if TOWN_NAME not in world.get_map().name:
        print(f"Switching server map to {TOWN_NAME}...")
        world = client.load_world(TOWN_NAME)

    blueprint_library = world.get_blueprint_library()
    fire_truck_bp = blueprint_library.find(FIRE_TRUCK_BLUEPRINT)
    fire_truck_bp.set_attribute("role_name", FIRE_TRUCK_ROLE_NAME)

    spawn_transform = carla.Transform(FIRE_TRUCK_LOCATION, FIRE_TRUCK_ROTATION)
    fire_truck = world.spawn_actor(fire_truck_bp, spawn_transform)

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
