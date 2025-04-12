from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler, LogInfo, EmitEvent, DeclareLaunchArgument
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true'
    )
    
    namespace_arg = DeclareLaunchArgument(
        'namespace',
        default_value='ezgripper',
        description='Namespace for the gripper'
    )
    
    output_topic_arg = DeclareLaunchArgument(
        'output_topic',
        default_value='/ezgripper/joint_states',
        description='Topic to publish joint states to'
    )
    
    prefix_arg = DeclareLaunchArgument(
        'prefix',
        default_value='',
        description='Prefix for joint names to match TF tree frame IDs'
    )
    
    
    # Gripper joint publisher node
    gripper_joint_publisher = Node(
        package='ezgripper_description',
        executable='gripper_joint_publisher',
        name='gripper_joint_publisher',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'prefix': LaunchConfiguration('prefix')
            }
        ],
        remappings=[
            ('/joint_states', LaunchConfiguration('output_topic'))
        ]
    )
    
    # Event handler for proper cleanup
    gripper_exit_handler = OnProcessExit(
        target_action=gripper_joint_publisher,
        on_exit=[
            LogInfo(msg=['Gripper joint publisher exited, shutting down launch']),
            EmitEvent(event=Shutdown(reason='Gripper joint publisher exited'))
        ]
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        namespace_arg,
        output_topic_arg,
        prefix_arg,
        
        # Nodes
        gripper_joint_publisher,
        
        # Event handlers
        RegisterEventHandler(gripper_exit_handler)
    ])
