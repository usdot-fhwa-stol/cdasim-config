from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    """
    Launch file for the lanelet2_map_loader node.
    """
    return LaunchDescription([
        DeclareLaunchArgument(
            name='lanelet2_map_file',
            default_value='/opt/carma/maps/vector_map.osm',
            description='Path to the lanelet2 map file'
        ),
        Node(
            package='lanelet2_map_loader',
            executable='lanelet2_map_loader_exec',
            name='lanelet2_map_loader',
            parameters=[
                {'lanelet2_map_file': LaunchConfiguration('lanelet2_map_file')},
                # This georeference is a standard default for CARMA simulation maps
                {'georeference': '+proj=tmerc +lat_0=38.95197911150576 +lon_0=-77.14835128349988 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +vunits=m +no_defs'}
            ]
        )
    ])