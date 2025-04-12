#!/usr/bin/env python3
"""
EZGripper Triple Integration - Launch File for Integration with Other Components
This launch file is designed to integrate the EZGripper Triple with other robot components
following the Linorobot2 architecture guidelines.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, LogInfo, EmitEvent
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Get package directories
    pkg_dir = get_package_share_directory('ezgripper_description')
    
    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time: "true" or "false"'
    )
    
    enable_hardware_arg = DeclareLaunchArgument(
        'enable_hardware',
        default_value='false',
        description='Enable hardware: "true" or "false"'
    )
    
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='ezgripper',
        description='Namespace for the gripper'
    )
    
    launch_joint_publisher_arg = DeclareLaunchArgument(
        'launch_joint_publisher',
        default_value='true',
        description='Whether to launch the gripper joint publisher'
    )
    
    launch_static_tf_publisher_arg = DeclareLaunchArgument(
        'launch_static_tf_publisher',
        default_value='true',
        description='Whether to launch the static TF publisher'
    )
    
    launch_robot_state_publisher_arg = DeclareLaunchArgument(
        'launch_robot_state_publisher',
        default_value='false',
        description='Whether to launch robot state publisher (should be false when integrated)'
    )
    
    # Joint state aggregator is no longer needed as we're using the robot_state_publisher directly
    
    prefix_arg = DeclareLaunchArgument(
        'prefix',
        default_value='gripper',
        description='Prefix for robot joint names'
    )
    
    # Unit numbers are now embedded in the xacro files and no longer needed as parameters
    
    # Include the triple gripper component launch file
    component_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'ezgripper_triple_description.launch.py')
        ),
        launch_arguments={
            # Always pass parameters as strings to avoid type conversion issues
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'enable_hardware': LaunchConfiguration('enable_hardware'),
            'namespace': LaunchConfiguration('namespace'),
            'launch_joint_publisher': LaunchConfiguration('launch_joint_publisher'),
            'launch_static_tf_publisher': LaunchConfiguration('launch_static_tf_publisher'),
            'launch_robot_state_publisher': LaunchConfiguration('launch_robot_state_publisher'),
            'prefix': LaunchConfiguration('prefix'),
            # Add rviz parameter explicitly to avoid empty tuple errors
            'rviz': 'false'
        }.items()
    )
    
    # Joint state merger has been removed as it's no longer needed
    # The robot_state_publisher handles joint state publishing directly
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        enable_hardware_arg,
        namespace_arg,
        launch_joint_publisher_arg,
        launch_static_tf_publisher_arg,
        launch_robot_state_publisher_arg,
        prefix_arg,
        
        # Include the triple gripper component
        component_launch
    ])

if __name__ == '__main__':
    generate_launch_description()
