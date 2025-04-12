#!/usr/bin/env python3
"""
Spawn Single EZGripper in RViz - Fixed version without joint_state_publisher_gui
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, RegisterEventHandler, LogInfo, EmitEvent
from launch_ros.actions import Node, PushRosNamespace
from launch.conditions import UnlessCondition, IfCondition
from launch.substitutions import LaunchConfiguration, Command
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_dir = get_package_share_directory('ezgripper_description')

    # Path to the URDF file
    urdf_file = os.path.join(pkg_dir, 'urdf', 'ezgripper_single_with_mount_standalone.urdf.xacro')

    # Define nodes
    joint_publisher = Node(
        package='ezgripper_description',
        executable='gripper_joint_publisher.py',
        name='gripper_joint_publisher',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        remappings=[
            ('/joint_states', '/gripper_joint_states')
        ],
        output='screen'
    )
    
    static_tf_publisher = Node(
        package='linorobot2_description',
        executable='gripper_static_tf_publisher',
        name='gripper_static_tf_publisher',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        output='screen'
    )
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='ezgripper_robot_state_publisher',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'robot_description': Command(['xacro', ' ', urdf_file])
            }
        ],
        output='screen',
        condition=UnlessCondition(LaunchConfiguration('use_sim_time'))
    )
    
    # Event handlers for proper cleanup
    joint_publisher_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_publisher,
            on_exit=[
                LogInfo(msg=['Joint publisher exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='Joint publisher exited'))
            ]
        )
    )
    
    static_tf_publisher_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=static_tf_publisher,
            on_exit=[
                LogInfo(msg=['Static TF publisher exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='Static TF publisher exited'))
            ]
        )
    )
    
    robot_state_publisher_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=robot_state_publisher,
            on_exit=[
                LogInfo(msg=['Robot state publisher exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='Robot state publisher exited'))
            ]
        ),
        condition=UnlessCondition(LaunchConfiguration('use_sim_time'))
    )
    
    # Global shutdown handler to ensure all processes are terminated
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                LogInfo(msg=['Shutting down EZGripper Single description fixed']),
                # Execute a cleanup command to kill any lingering processes
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
        # Declare launch arguments
        DeclareLaunchArgument(
            'namespace',
            default_value='ezgripper',
            description='Namespace for the gripper'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time: "true" or "false"'
        ),

        # Group actions under the namespace
        GroupAction([
            PushRosNamespace(LaunchConfiguration('namespace')),
            joint_publisher,
            static_tf_publisher,
            robot_state_publisher
        ]),
        
        # Event handlers
        joint_publisher_exit_handler,
        static_tf_publisher_exit_handler,
        robot_state_publisher_exit_handler,
        shutdown_handler
    ])
