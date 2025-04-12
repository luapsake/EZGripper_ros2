#!/usr/bin/env python3
"""
EZGripper Standalone - Launch File for Independent Operation
This launch file runs the EZGripper component independently with its own
robot state publisher and visualization.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, LogInfo, EmitEvent
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Get package directories
    pkg_dir = get_package_share_directory('ezgripper_description')
    
    # Path to the URDF file
    urdf_file = os.path.join(pkg_dir, 'urdf', 'ezgripper_single_with_mount_standalone.urdf.xacro')
    rviz_config_path = os.path.join(pkg_dir, 'rviz', 'urdf.rviz')
    
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
    
    prefix_arg = DeclareLaunchArgument(
        'prefix',
        default_value='left_arm',
        description='Prefix for joint names to match TF tree frame IDs'
    )
    
    
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Launch RViz: "true" or "false"'
    )
    
    # Include the base component launch file
    component_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'ezgripper_description.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'namespace': LaunchConfiguration('namespace'),
            'prefix': LaunchConfiguration('prefix'),
            'launch_joint_publisher': 'true',
            'launch_static_tf_publisher': 'true'
        }.items()
    )
    
    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=LaunchConfiguration('namespace'),
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'robot_description': ParameterValue(Command(['xacro', ' ', urdf_file, ' prefix:=', LaunchConfiguration('prefix')]), value_type=str)
            }
        ],
        remappings=[
            ('/joint_states', '/ezgripper/joint_states')
        ]
    )
    
    # Launch RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
        condition=IfCondition(LaunchConfiguration('rviz'))
    )
    
    # Event handlers for proper cleanup
    robot_state_publisher_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=robot_state_publisher,
            on_exit=[
                LogInfo(msg=['Robot state publisher exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='Robot state publisher exited'))
            ]
        )
    )
    
    # RViz exit handler
    rviz_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=rviz_node,
            on_exit=[
                LogInfo(msg=['RViz exited, shutting down launch']),
                EmitEvent(event=Shutdown(reason='RViz exited'))
            ]
        )
    )
    
    # Shutdown handler for SIGINT (Ctrl+C)
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                LogInfo(msg=['Launch was asked to shutdown: stopping all nodes']),
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
        # Launch arguments
        use_sim_time_arg,
        namespace_arg,
        prefix_arg,
        rviz_arg,
        
        # Include component launch
        component_launch,
        
        # Nodes
        robot_state_publisher,
        rviz_node,
        
        # Event handlers
        robot_state_publisher_exit_handler,
        rviz_exit_handler,
        shutdown_handler
    ])
