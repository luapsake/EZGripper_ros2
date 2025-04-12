#!/usr/bin/env python3
"""
EZGripper Description - Base Component Launch File
This is the base component launch file for the EZGripper that follows
the Linorobot2 architecture guidelines.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, LogInfo, EmitEvent
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
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
    
    # Gripper joint publisher node
    gripper_joint_publisher = Node(
        package='ezgripper_description',
        executable='gripper_joint_publisher',
        name='gripper_joint_publisher',  # Updated name to match the executable
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        # Removed unnecessary remapping since we're publishing directly to /ezgripper/joint_states
        condition=IfCondition(LaunchConfiguration('launch_joint_publisher'))
    )
    
    # Gripper static TF publisher node
    gripper_static_tf_publisher = Node(
        package='ezgripper_description',
        executable='gripper_static_tf_publisher',
        name='gripper_static_tf_publisher',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time')
            }
        ],
        condition=IfCondition(LaunchConfiguration('launch_static_tf_publisher'))
    )
    
    # Event handlers for proper cleanup
    gripper_joint_publisher_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=gripper_joint_publisher,
            on_exit=[
                LogInfo(msg=['Gripper joint publisher exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='Gripper joint publisher exited'))
            ]
        )
    )
    
    gripper_static_tf_publisher_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=gripper_static_tf_publisher,
            on_exit=[
                LogInfo(msg=['Gripper static TF publisher exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='Gripper static TF publisher exited'))
            ]
        )
    )
    
    # Shutdown handler for SIGINT (Ctrl+C)
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                LogInfo(msg=['Launch was asked to shutdown: stopping all nodes'])
            ]
        )
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        namespace_arg,
        launch_joint_publisher_arg,
        launch_static_tf_publisher_arg,
        
        # Nodes
        gripper_joint_publisher,
        gripper_static_tf_publisher,
        
        # Event handlers
        gripper_joint_publisher_exit_handler,
        gripper_static_tf_publisher_exit_handler,
        shutdown_handler
    ])
