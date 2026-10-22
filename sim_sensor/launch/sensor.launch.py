import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    params = os.path.join(get_package_share_directory('sim_sensor'),
                          'config', 'params.yaml')
    return LaunchDescription([
        DeclareLaunchArgument('rate_hz', default_value='10.0',
                              description='Publish rate in Hz (0.1 - 100)'),
        DeclareLaunchArgument('autostart', default_value='true',
                              description='Begin publishing on startup'),
        Node(
            package='sim_sensor',
            executable='sensor_node',
            name='sim_sensor',
            output='screen',
            # Later entries override earlier ones: YAML first, CLI args on top.
            parameters=[params, {
                'rate_hz': LaunchConfiguration('rate_hz'),
                'autostart': LaunchConfiguration('autostart'),
            }],
        ),
    ])
