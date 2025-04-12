#!/usr/bin/env python3
"""Static TF Publisher for EZGripper
This node publishes static transforms for the EZGripper components that don't move.
For the underactuated EZGripper, only the palm to L1 joints are actuated.
The L1 to L2 joints and finger pad joints are fixed and published as static transforms.
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster, Buffer, TransformListener
import yaml
import os
import sys
import math
import re
import time
from ament_index_python.packages import get_package_share_directory

# Try to import prctl for process naming
try:
    import prctl
    HAS_PRCTL = True
except ImportError:
    HAS_PRCTL = False

class GripperStaticTFPublisher(Node):
    def __init__(self):
        super().__init__('gripper_static_tf_publisher')
        
        # Create a static transform broadcaster
        self.static_broadcaster = StaticTransformBroadcaster(self)
        
        # Setup TF listener for frame detection
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Load the static transforms from the YAML configuration
        self.get_logger().info('Creating static transforms for EZGripper components')
        
        # Wait a moment for the TF tree to be populated
        time.sleep(1.0)
        
        # Create static transforms for the EZGripper components
        self.create_static_transforms()
        
    def create_static_transforms(self):
        """Create static transforms for the EZGripper components
        
        This method only handles the static (non-moving) parts of the gripper:
        - The L1 to L2 finger links
        - The finger pads
        
        The dynamic transforms (palm to knuckle joints) are handled by robot_state_publisher
        based on the joint states published by gripper_joint_publisher.py.
        """
        # Get the prefix (arm name) from the parameters
        self.declare_parameter('prefix', 'gripper')
        
        # Get the prefix parameter
        prefix = self.get_parameter('prefix').value
        
        # Log the prefix being used
        self.get_logger().info(f'Using prefix "{prefix}" for frame IDs')
        
        # Try to detect palm links from the URDF or TF tree
        palm_links = self.detect_palm_links(prefix)
        
        if palm_links:
            self.get_logger().info(f'Found {len(palm_links)} palm links: {palm_links}')
            
            # Create static transforms for each detected palm link
            for palm_link in palm_links:
                # Extract the prefix from the palm link name
                # Format could be either prefix_ezgripper_palm_link or prefix_N_ezgripper_palm_link
                if '_ezgripper_palm_link' in palm_link:
                    # Extract the prefix by removing the '_ezgripper_palm_link' suffix
                    gripper_prefix = palm_link.replace('_ezgripper_palm_link', '')
                    self.get_logger().info(f'Creating static transforms for {gripper_prefix}')
                    self.create_finger_transforms(gripper_prefix)
                else:
                    self.get_logger().warn(f'Unexpected palm link format: {palm_link}')
        else:
            # Fallback to using the provided prefix
            if prefix:
                self.get_logger().info(f'No palm links detected, using provided prefix: {prefix}')
                self.create_finger_transforms(f'{prefix}_ezgripper')
            else:
                # If no prefix and no palm links, use a default prefix
                self.get_logger().info('No prefix provided and no palm links detected, using default prefix: gripper')
                self.create_finger_transforms('gripper_ezgripper')
    

    def detect_palm_links(self, prefix):
        """Detect palm links from the robot description or TF tree
        
        Args:
            prefix: The prefix to filter palm links by (optional)
            
        Returns:
            list: List of palm link names
        """
        try:
            # Try to get the robot description parameter
            self.declare_parameter('robot_description', '')
            robot_description = self.get_parameter('robot_description').value
            
            # If we have a robot description, parse it to find palm links
            # Each ezgripper_single.urdf.xacro instance will have a palm link with pattern ${prefix}_ezgripper_palm_link
            if robot_description:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(robot_description)
                
                # Find all links that match the palm link pattern
                palm_links = []
                for link in root.findall('.//link'):
                    link_name = link.get('name', '')
                    if 'ezgripper_palm_link' in link_name:
                        # If prefix is provided, filter by prefix
                        if not prefix or (prefix and link_name.startswith(prefix)):
                            palm_links.append(link_name)
                            self.get_logger().info(f'Found palm link in URDF: {link_name}')
                
                if palm_links:
                    self.get_logger().info(f'Found {len(palm_links)} palm links in robot description')
                    return palm_links
                else:
                    self.get_logger().warn('No palm links found in robot description')
            
            # If we don't have a robot description or didn't find any palm links,
            # try to detect them from the TF tree
            # The TF tree should have frames that match the pattern ${prefix}_ezgripper_palm_link
            self.get_logger().info('Trying to detect palm links from TF tree')
            
            # Get all frames in the TF tree
            all_frames = []
            frames_str = self.tf_buffer.all_frames_as_string()
            
            # Look for frames that match the palm link pattern
            palm_links = []
            for line in frames_str.split('\n'):
                line = line.strip()
                if line and 'ezgripper_palm_link' in line:
                    # Extract the frame name
                    import re
                    match = re.search(r'Frame ([^ ]+) exists', line)
                    if match:
                        frame_name = match.group(1)
                        all_frames.append(frame_name)
                        # If prefix is provided, filter by prefix
                        if not prefix or (prefix and frame_name.startswith(prefix)):
                            palm_links.append(frame_name)
                            self.get_logger().info(f'Found palm link in TF tree: {frame_name}')
            
            if palm_links:
                self.get_logger().info(f'Found {len(palm_links)} palm links in TF tree')
                return palm_links
            
            # If we still don't have any palm links, create default ones based on the prefix
            # Each ezgripper_single instance has a consistent naming pattern
            if prefix:
                # Create a single palm link with the provided prefix
                palm_link = f'{prefix}_ezgripper_palm_link'
                self.get_logger().info(f'Using default palm link based on provided prefix: {palm_link}')
                return [palm_link]
            else:
                # Default to a single gripper with default prefix
                palm_link = 'gripper_ezgripper_palm_link'
                self.get_logger().info(f'Using default palm link with default prefix: {palm_link}')
                return [palm_link]
            
        except Exception as e:
            self.get_logger().error(f'Error detecting palm links: {str(e)}')
            # Return a default palm link as fallback
            if prefix:
                return [f'{prefix}_ezgripper_palm_link']
            else:
                return ['gripper_ezgripper_palm_link']
    
    def create_finger_transforms(self, prefix):
        """Create static transforms for a gripper's fingers based on the ezgripper_single.urdf.xacro structure.
        
        Each ezgripper_single instance has:
        - A palm link: ${prefix}_ezgripper_palm_link
        - Two knuckle joints: ${prefix}_ezgripper_knuckle_palm_L1_1 and ${prefix}_ezgripper_knuckle_palm_L1_2
        - Corresponding finger links and pads
        
        Note: For the underactuated EZGripper, only the palm to L1 joints are actuated.
        The L1 to L2 joints and finger pad joints are fixed and published as static transforms.
        
        This method only handles the static (non-moving) transforms:
        - knuckle to finger L1
        - L1 to L2
        - L2 to finger pad
        
        The dynamic transforms (palm to knuckle) are handled by robot_state_publisher
        based on the joint states published by gripper_joint_publisher.py.
        """
        # Ensure we have the correct prefix format with _ezgripper
        if not '_ezgripper' in prefix:
            full_prefix = f'{prefix}_ezgripper'
        else:
            full_prefix = prefix
            
        self.get_logger().info(f'Creating static transforms for gripper with prefix: {full_prefix}')
        
        # Create transforms based on the URDF structure in ezgripper_single.urdf.xacro
        # Note: We skip the palm to knuckle joints as they are dynamic (actuated)
        
        # Fixed transforms for the finger links
        # First finger chain
        self.publish_static_transform(
            parent_frame=f'{full_prefix}_knuckle_palm_L1_1',
            child_frame=f'{full_prefix}_finger_L1_1',
            x=0.0, y=0.0, z=0.0,
            roll=0.0, pitch=0.0, yaw=0.0  # Original orientation
        )
        
        self.publish_static_transform(
            parent_frame=f'{full_prefix}_finger_L1_1',
            child_frame=f'{full_prefix}_finger_L2_1',
            x=0.052, y=0.0, z=0.0,  # From URDF: L1 to L2 distance
            roll=0.0, pitch=0.0, yaw=0.0
        )
        
        self.publish_static_transform(
            parent_frame=f'{full_prefix}_finger_L2_1',
            child_frame=f'{full_prefix}_finger_pad_1',
            x=0.01849, y=0.0, z=0.0,  # From URDF: L2 to pad distance
            roll=0.0, pitch=-0.23, yaw=0.0  # From URDF: pad angle
        )
            
        # Second finger chain
        self.publish_static_transform(
            parent_frame=f'{full_prefix}_knuckle_palm_L1_2',
            child_frame=f'{full_prefix}_finger_L1_2',
            x=0.0, y=0.0, z=0.0,
            roll=0.0, pitch=0.0, yaw=0.0  # Original orientation
        )
        
        self.publish_static_transform(
            parent_frame=f'{full_prefix}_finger_L1_2',
            child_frame=f'{full_prefix}_finger_L2_2',
            x=0.052, y=0.0, z=0.0,  # From URDF: L1 to L2 distance
            roll=0.0, pitch=0.0, yaw=0.0
        )
        
        self.publish_static_transform(
            parent_frame=f'{full_prefix}_finger_L2_2',
            child_frame=f'{full_prefix}_finger_pad_2',
            x=0.01849, y=0.0, z=0.0,  # From URDF: L2 to pad distance
            roll=0.0, pitch=-0.23, yaw=0.0  # From URDF: pad angle
        )
        
        self.get_logger().info(f'Created static transforms for {full_prefix} fingers')
        
    def publish_static_transform(self, parent_frame, child_frame, x, y, z, roll, pitch, yaw):
        """Publish a static transform
        
        Args:
            parent_frame: Parent frame ID
            child_frame: Child frame ID
            x, y, z: Translation
            roll, pitch, yaw: Rotation in radians
        """
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = parent_frame
        transform.child_frame_id = child_frame
        
        # Set translation
        transform.transform.translation.x = x
        transform.transform.translation.y = y
        transform.transform.translation.z = z
        
        # Set rotation using quaternion
        # Simple conversion from Euler angles to quaternion
        # This is a simplified version, for more accuracy use tf_transformations
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        transform.transform.rotation.w = cy * cp * cr + sy * sp * sr
        transform.transform.rotation.x = cy * cp * sr - sy * sp * cr
        transform.transform.rotation.y = sy * cp * sr + cy * sp * cr
        transform.transform.rotation.z = sy * cp * cr - cy * sp * sr
        
        # Publish the transform
        self.static_broadcaster.sendTransform(transform)
        self.get_logger().info(f'Created static transform from {parent_frame} to {child_frame}')
        


def main(args=None):
    # Set process name for better identification in system tools
    if HAS_PRCTL:
        prctl.set_name("gripper_static_tf")
        prctl.set_proctitle("gripper_static_tf_publisher")
    else:
        # Alternative method using setproctitle if available
        try:
            from setproctitle import setproctitle
            setproctitle("gripper_static_tf_publisher")
        except ImportError:
            # If neither method is available, we can still set the process title for ps
            try:
                # This only works on Linux
                os.environ['_'] = "gripper_static_tf_publisher"
            except Exception:
                pass
    
    rclpy.init(args=args)
    node = GripperStaticTFPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception as e:
            # Ignore shutdown errors - this happens when shutdown is called multiple times
            # or when the context is already shutting down
            pass

if __name__ == '__main__':
    main()
