#!/usr/bin/env python3
"""Print vehicle downtrack and nearest-pedestrian distance from ROS 2 topics."""

import math

import rclpy
from carma_cooperative_perception_interfaces.msg import DetectionList
from carma_planning_msgs.msg import RouteState
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.qos import QoSProfile, qos_profile_sensor_data


PEDESTRIAN_CLASS = 3


class VehiclePedDistanceMonitor(Node):
    def __init__(self) -> None:
        super().__init__("vehicle_ped_distance_monitor")

        self.declare_parameter("route_state_topic", "/guidance/route_state")
        self.declare_parameter("vehicle_pose_topic", "/localization/current_pose")
        self.declare_parameter("detection_topic", "/environment/full_detection_list")
        self.declare_parameter("print_rate_hz", 5.0)
        self.declare_parameter("detection_timeout_sec", 1.0)

        route_state_topic = self.get_parameter("route_state_topic").value
        vehicle_pose_topic = self.get_parameter("vehicle_pose_topic").value
        detection_topic = self.get_parameter("detection_topic").value
        print_rate_hz = float(self.get_parameter("print_rate_hz").value)
        self.detection_timeout_sec = float(
            self.get_parameter("detection_timeout_sec").value
        )

        if print_rate_hz <= 0.0:
            raise ValueError("print_rate_hz must be greater than zero")

        self.vehicle_downtrack = None
        self.vehicle_position = None
        self.pedestrians = []
        self.last_detection_time = None

        self.create_subscription(
            RouteState,
            route_state_topic,
            self.route_state_callback,
            QoSProfile(depth=10),
        )
        self.create_subscription(
            PoseStamped,
            vehicle_pose_topic,
            self.vehicle_pose_callback,
            qos_profile_sensor_data,
        )
        self.create_subscription(
            DetectionList,
            detection_topic,
            self.detection_callback,
            qos_profile_sensor_data,
        )
        self.create_timer(1.0 / print_rate_hz, self.print_status)

    def route_state_callback(self, message: RouteState) -> None:
        self.vehicle_downtrack = float(message.down_track)

    def vehicle_pose_callback(self, message: PoseStamped) -> None:
        position = message.pose.position
        self.vehicle_position = (float(position.x), float(position.y))

    def detection_callback(self, message: DetectionList) -> None:
        self.pedestrians = []
        for detection in message.detections:
            if detection.semantic_class != PEDESTRIAN_CLASS:
                continue

            position = detection.pose.pose.position
            self.pedestrians.append(
                (
                    str(detection.id),
                    float(position.x),
                    float(position.y),
                )
            )

        self.last_detection_time = self.get_clock().now()

    def nearest_pedestrian(self):
        if self.vehicle_position is None or self.last_detection_time is None:
            return None

        detection_age = (
            self.get_clock().now() - self.last_detection_time
        ).nanoseconds / 1e9
        if detection_age > self.detection_timeout_sec:
            return None

        vehicle_x, vehicle_y = self.vehicle_position
        nearest = None
        for pedestrian_id, pedestrian_x, pedestrian_y in self.pedestrians:
            distance = math.hypot(
                pedestrian_x - vehicle_x,
                pedestrian_y - vehicle_y,
            )
            candidate = (distance, pedestrian_id, pedestrian_x, pedestrian_y)
            if nearest is None or candidate[0] < nearest[0]:
                nearest = candidate

        return nearest

    def print_status(self) -> None:
        if self.vehicle_downtrack is None:
            print(
                "vehicle_downtrack_m=NA pedestrian_distance_m=NA "
                "status=waiting_for_route_state",
                flush=True,
            )
            return

        nearest = self.nearest_pedestrian()
        if nearest is None:
            print(
                f"vehicle_downtrack_m={self.vehicle_downtrack:.2f} "
                "pedestrian_distance_m=NA status=no_current_pedestrian",
                flush=True,
            )
            return

        distance, pedestrian_id, pedestrian_x, pedestrian_y = nearest
        print(
            f"vehicle_downtrack_m={self.vehicle_downtrack:.2f} "
            f"pedestrian_distance_m={distance:.2f} "
            f"pedestrian_id={pedestrian_id} "
            f"pedestrian_xy=({pedestrian_x:.2f},{pedestrian_y:.2f})",
            flush=True,
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = VehiclePedDistanceMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
