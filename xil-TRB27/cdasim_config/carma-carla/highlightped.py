
#!/usr/bin/env python3

import carla
import math
import time

# ========== Configuration ==========
HOST = "127.0.0.1"
PORT = 2000

UPDATE_INTERVAL = 0.05
MARKER_LIFETIME = 0.3

BURIED_DEPTH = 1.0
MAX_ROAD_DISTANCE = 5.0
FALLBACK_HEIGHT = 50.0
# ===================================

RED = carla.Color(255, 0, 0)
YELLOW = carla.Color(255, 255, 0)
MAGENTA = carla.Color(255, 0, 255)
CYAN = carla.Color(0, 255, 255)


def point(x, y, z):
    return carla.Location(x=x, y=y, z=z)


def get_surface(world_map, location):
    try:
        wp = world_map.get_waypoint(
            location,
            project_to_road=True,
            lane_type=carla.LaneType.Any
        )

        if wp is None:
            return None

        p = wp.transform.location

        distance = math.hypot(
            p.x - location.x,
            p.y - location.y
        )

        if distance > MAX_ROAD_DISTANCE:
            return None

        return p.z

    except RuntimeError:
        return None


def highlight(world, walker, world_map):
    debug = world.debug

    tf = walker.get_transform()
    loc = tf.location
    bbox = walker.bounding_box

    # Real actor bounding box
    center = tf.transform(bbox.location)

    box = carla.BoundingBox(
        center,
        carla.Vector3D(
            max(0.35, bbox.extent.x * 1.5),
            max(0.35, bbox.extent.y * 1.5),
            max(0.9, bbox.extent.z * 1.1)
        )
    )

    debug.draw_box(
        box,
        tf.rotation,
        thickness=0.2,
        color=RED,
        life_time=MARKER_LIFETIME
    )

    # Estimate ground height
    surface_z = get_surface(world_map, loc)

    buried = (
        surface_z is not None
        and loc.z < surface_z - BURIED_DEPTH
    )

    if surface_z is None:
        surface_z = loc.z + FALLBACK_HEIGHT

    x = loc.x
    y = loc.y
    base_z = surface_z + 0.5

    # Large yellow vertical marker
    debug.draw_line(
        point(x, y, base_z),
        point(x, y, base_z + 7),
        thickness=0.25,
        color=YELLOW,
        life_time=MARKER_LIFETIME
    )

    # Large red downward arrow
    debug.draw_arrow(
        point(x, y, base_z + 10),
        point(x, y, base_z + 7),
        thickness=0.3,
        arrow_size=1.2,
        color=RED,
        life_time=MARKER_LIFETIME
    )

    # Three magenta square markers
    for height, radius in [
        (0.5, 1.7),
        (1.0, 1.4),
        (1.5, 1.1)
    ]:
        z = base_z + height

        corners = [
            point(x-radius, y-radius, z),
            point(x+radius, y-radius, z),
            point(x+radius, y+radius, z),
            point(x-radius, y+radius, z)
        ]

        for i in range(4):
            debug.draw_line(
                corners[i],
                corners[(i + 1) % 4],
                thickness=0.16,
                color=MAGENTA,
                life_time=MARKER_LIFETIME
            )

    # Cyan position indicator
    debug.draw_point(
        point(x, y, base_z + 7),
        size=0.45,
        color=CYAN,
        life_time=MARKER_LIFETIME
    )

    # Actor ID
    if buried:
        label = f"UNDERGROUND PED [{walker.id}]"
    else:
        label = f"PEDESTRIAN [{walker.id}]"

    debug.draw_string(
        point(x, y, base_z + 11),
        label,
        draw_shadow=True,
        color=YELLOW,
        life_time=MARKER_LIFETIME
    )

    return buried


def main():
    client = carla.Client(HOST, PORT)
    client.set_timeout(10.0)

    world = client.get_world()
    world_map = world.get_map()

    print("Connected to CARLA")
    print("Tracking pedestrians...")

    try:
        while True:
            walkers = world.get_actors().filter(
                "walker.pedestrian.*"
            )

            buried_count = 0

            for walker in walkers:
                try:
                    if not walker.is_alive:
                        continue

                    if highlight(world, walker, world_map):
                        buried_count += 1

                except RuntimeError:
                    continue

            print(
                f"\rPedestrians: {len(walkers)} | "
                f"Underground: {buried_count}",
                end="",
                flush=True
            )

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
