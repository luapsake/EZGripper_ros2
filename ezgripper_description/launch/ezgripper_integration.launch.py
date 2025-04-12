#!/usr/bin/env python3
"""
EZGripper Integration - Launch File for Integration with Other Components
This launch file is designed to integrate the EZGripper with other robot components
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
    
    # Include the base component launch file
    component_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'ezgripper_description.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': LaunchConfiguration('namespace'),
            'launch_joint_publisher': LaunchConfiguration('launch_joint_publisher'),
            'launch_static_tf_publisher': LaunchConfiguration('launch_static_tf_publisher')
        }.items()
    )
    
    # Joint state merger has been removed as it's no longer needed
    # The robot_state_publisher handles joint state publishing directly
    
    # Global shutdown handler to ensure all processes are terminated
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                LogInfo(msg=['Shutting down EZGripper integration']),
                # Execute a cleanup command to kill any lingering processes
                # This ensures no orphaned processes remain
                Node(
                    package='ezgripper_description',
                    executable='cleanup_ezgripper_processes.py',
                    name='cleanup_ezgripper_processes',
                    output='screen'
                )
            ]
        )
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        namespace_arg,
        launch_joint_publisher_arg,
        launch_static_tf_publisher_arg,
        launch_robot_state_publisher_arg,
        
        # Include component launch
        component_launch,
        
        # Add the shutdown handler
        shutdown_handler
    ])
