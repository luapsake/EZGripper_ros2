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
    
    prefix_arg = DeclareLaunchArgument(
        'prefix',
        default_value='',
        description='Arm name for the gripper assembly (e.g., left_arm, right_arm)'
    )
    
    # Gripper static TF publisher node
    gripper_static_tf_publisher = Node(
        package='ezgripper_description',
        executable='gripper_static_tf_publisher',
        name='gripper_static_tf_publisher',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'prefix': LaunchConfiguration('prefix')
        }]
    )
    
    # Event handler for proper cleanup
    gripper_tf_exit_handler = OnProcessExit(
        target_action=gripper_static_tf_publisher,
        on_exit=[
            LogInfo(msg=['Gripper static TF publisher exited, shutting down launch']),
            EmitEvent(event=Shutdown(reason='Gripper static TF publisher exited'))
        ]
    )
    
    return LaunchDescription([
        # Launch arguments
        use_sim_time_arg,
        namespace_arg,
        prefix_arg,
        
        # Nodes
        gripper_static_tf_publisher,
        
        # Event handlers
        RegisterEventHandler(gripper_tf_exit_handler)
    ])
