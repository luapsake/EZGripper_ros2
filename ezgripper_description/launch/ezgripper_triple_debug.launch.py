#!/usr/bin/env python3
"""
EZGripper Triple Debug Launch File

This launch file is designed to debug the triple gripper launch issues
by using a more direct approach to process the XACRO file.
"""
import os
import subprocess
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, LogInfo, EmitEvent
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    """
    Launch Function for Triple EZGripper Debug
    """
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
    
    prefix_arg = DeclareLaunchArgument(
        'prefix',
        default_value='gripper',
        description='Prefix for the gripper (arm name)'
    )
    
    # Define URDF file path
    urdf_file = os.path.join(pkg_dir, 'urdf', 'ezgripper_triple_with_mount_standalone.urdf.xacro')
    
    # Create a custom command to process the XACRO file
    # This uses a simple string concatenation approach that's more reliable
    xacro_command = Command([
        'xacro', urdf_file, 
        'prefix:=', LaunchConfiguration('prefix')
    ])
    
    # Start Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'robot_description': ParameterValue(xacro_command, value_type=str),
            }
        ],
        remappings=[
            ('/joint_states', ['/', LaunchConfiguration('namespace'), '/joint_states'])
        ],
    )
    
    # Start Joint State Publisher
    joint_state_publisher = Node(
        package='ezgripper_description',
        executable='gripper_joint_publisher.py',
        name='gripper_joint_publisher',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'enable_hardware': LaunchConfiguration('enable_hardware')},
            {'namespace': LaunchConfiguration('namespace')},
            {'prefix': LaunchConfiguration('prefix')},
        ],
    )
    
    # Start RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', os.path.join(pkg_dir, 'rviz', 'urdf.rviz')],
    )
    
    # Add event handler for proper cleanup when RViz exits
    rviz_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=rviz_node,
            on_exit=[
                LogInfo(msg=['RViz exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='RViz exited'))
            ]
        )
    )
    
    # Add shutdown handler
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                LogInfo(msg=['Launch shutting down'])
            ]
        )
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        enable_hardware_arg,
        namespace_arg,
        prefix_arg,
        
        # Nodes
        robot_state_publisher,
        joint_state_publisher,
        rviz_node,
        
        # Event handlers
        rviz_exit_handler,
        shutdown_handler,
    ])
