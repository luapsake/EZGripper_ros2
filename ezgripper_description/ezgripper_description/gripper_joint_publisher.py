#!/usr/bin/env python3
"""
EZGripper Joint Position Publisher
Publishes joint positions for the EZGripper based on arm_name identification
"""
import os
import re
import yaml
import time
import rclpy
from rclpy.node import Node
from rclpy.time import Duration
from std_msgs.msg import Float64, Float32
from sensor_msgs.msg import JointState
from tf2_ros import Buffer, TransformListener
from ament_index_python.packages import get_package_share_directory

class GripperJointPublisher(Node):
    def __init__(self):
        super().__init__('gripper_joint_publisher')
        
        # Setup TF listener for frame detection
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Check for prefix parameter
        self.declare_parameter('prefix', 'left_arm')
        
        # Get the prefix parameter
        self.prefix = self.get_parameter('prefix').value
        
        # Log warning if prefix is empty
        if not self.prefix:
            self.get_logger().warn('Prefix parameter is empty! Using default prefix: left_arm')
            self.prefix = 'left_arm'
        
        self.get_logger().info(f'Using prefix: {self.prefix}')
            
        # Load controller configuration to get joint names
        pkg_share = get_package_share_directory('ezgripper_description')
        controllers_yaml_path = os.path.join(pkg_share, 'config', 'ezgripper_controllers.yaml')
        
        self.get_logger().info(f'Loading controller configuration from {controllers_yaml_path}')
        with open(controllers_yaml_path, 'r') as file:
            controller_config = yaml.safe_load(file)

        # Extract joint names from configuration
        joint_names = []
        for controller, params in controller_config.items():
            if 'ros__parameters' in params and 'joint' in params['ros__parameters']:
                joint_name = params['ros__parameters']['joint']
                joint_names.append(joint_name)
                self.get_logger().info(f'Found joint from controller config: {joint_name}')
        
        # Create empty lists for the new joint names and positions
        new_joint_names = []
        new_joint_positions = []
        new_joint_velocities = []
        new_joint_efforts = []
        
        # Publisher for the component-level joint states only
        # Do NOT publish to global joint_states - that should be handled by the launch hierarchy
        self.publisher = self.create_publisher(JointState, '/ezgripper/joint_states', 10)
        self.get_logger().info('Publisher created for /ezgripper/joint_states')

        # Create a dictionary to map joint names to their respective indexes
        # This will be populated after we have the final list of joint names
        
        # Group joints by gripper prefix
        self.grippers = set()  # Set of prefix strings
        self.gripper_to_joints = {}
        
        # Regular expression patterns to match joint naming conventions
        # Format for single gripper: prefix_ezgripper_knuckle_palm_L1_finger_num
        # Example: gripper_ezgripper_knuckle_palm_L1_1 (gripper, finger 1)
        # 
        # Format for double/triple gripper: prefix_num_ezgripper_knuckle_palm_L1_finger_num
        # Example: gripper_1_ezgripper_knuckle_palm_L1_1 (gripper 1, finger 1)
        #
        # Note: The TF tree uses gripper_N_ prefix format for triple gripper
        
        # Two patterns to match both single and multi-gripper configurations
        single_gripper_pattern = r'([^_]+)_ezgripper_knuckle_palm_L1_([^_]+)'
        multi_gripper_pattern = r'([^_]+)_([^_]+)_ezgripper_knuckle_palm_L1_([^_]+)'
        # Create joint names directly based on the URDF naming convention
        # For the triple gripper, we need to create joint names for all three grippers
        joint_names = []
        
        # Base gripper joints
        base_joints = [
            f'{self.prefix}_ezgripper_knuckle_palm_L1_1',
            f'{self.prefix}_ezgripper_knuckle_palm_L1_2',
            f'{self.prefix}_ezgripper_knuckle_palm_L1_3'
        ]
        joint_names.extend(base_joints)
        
        # Numbered gripper joints (1, 2, 3) for triple configuration
        for i in range(1, 4):
            numbered_joints = [
                f'{self.prefix}_{i}_ezgripper_knuckle_palm_L1_1',
                f'{self.prefix}_{i}_ezgripper_knuckle_palm_L1_2',
                f'{self.prefix}_{i}_ezgripper_knuckle_palm_L1_3'
            ]
            joint_names.extend(numbered_joints)
        
        self.get_logger().info(f'Created joint names based on URDF naming convention: {joint_names}')
        
        # Create a mapping from controller joint names to actual joint names with the correct prefix
        self.controller_to_actual_joint = {}
        
        # Create new joint names using the correct prefix
        new_joint_names = []
        new_joint_positions = []
        new_joint_velocities = []
        new_joint_efforts = []
        
        for joint_name in joint_names:
            # Use the joint name as is - we're getting them directly from the TF tree
            # or generating them with the correct prefix already
            new_joint_name = joint_name
            self.get_logger().info(f'Using joint name: {new_joint_name}')
            
            # Map the original joint name to the new joint name
            self.controller_to_actual_joint[joint_name] = new_joint_name
            
            # Add the new joint name to our lists
            new_joint_names.append(new_joint_name)
            new_joint_positions.append(0.0)
            new_joint_velocities.append(0.0)
            new_joint_efforts.append(0.0)
            
            # Add this prefix to our set of grippers
            self.grippers.add(self.prefix)
            
            if self.prefix not in self.gripper_to_joints:
                self.gripper_to_joints[self.prefix] = []
            
            self.gripper_to_joints[self.prefix].append(new_joint_name)
            self.get_logger().info(f'Added joint {new_joint_name} to gripper with prefix {self.prefix}')
        
        # Ensure we don't have duplicate joint names
        unique_joint_names = []
        unique_joint_positions = []
        unique_joint_velocities = []
        unique_joint_efforts = []
        
        # Use a set to track which joint names we've already added
        added_joints = set()
        
        for i, joint_name in enumerate(new_joint_names):
            if joint_name not in added_joints:
                added_joints.add(joint_name)
                unique_joint_names.append(joint_name)
                unique_joint_positions.append(new_joint_positions[i] if i < len(new_joint_positions) else 0.0)
                unique_joint_velocities.append(new_joint_velocities[i] if i < len(new_joint_velocities) else 0.0)
                unique_joint_efforts.append(new_joint_efforts[i] if i < len(new_joint_efforts) else 0.0)
                self.get_logger().info(f'Added unique joint: {joint_name}')
        
        # Create a dictionary to map joint names to their respective indexes
        self.joint_indexes = {name: i for i, name in enumerate(unique_joint_names)}
        
        # Initialize joint state message with the unique joint names
        self.joint_state = JointState()
        self.joint_state.name = unique_joint_names
        self.joint_state.position = unique_joint_positions
        self.joint_state.velocity = unique_joint_velocities
        self.joint_state.effort = unique_joint_efforts
        
        self.get_logger().info(f'Final unique joints: {unique_joint_names}')
        
        # Check if we have any grippers with empty prefixes and warn about it
        for prefix in list(self.grippers):
            if not prefix or prefix == '_':
                self.get_logger().warn(f'Found gripper with empty prefix: {prefix}')
                self.get_logger().warn('This will cause incorrect joint naming and control issues.')
                self.get_logger().warn('Please specify a prefix (arm name) when launching the node.')
        
        # Create independent subscribers for each gripper
        self.subscribers = []
        
        # Group joints by gripper identifier
        gripper_groups = {}
        
        # Parse joint names to identify which gripper they belong to
        for joint_name in joint_names:
            # Extract gripper identifier from the joint name
            # Use everything before _ezgripper as the gripper ID
            match = re.search(r'(.+)_ezgripper', joint_name)
            if match:
                gripper_id = match.group(1)
                self.get_logger().info(f'Identified gripper joint: {joint_name} -> gripper_id: {gripper_id}')
            else:
                # If no pattern matches, use a default identifier
                gripper_id = self.prefix
                self.get_logger().warn(f'Could not identify gripper pattern for joint: {joint_name}, using default "{self.prefix}"')
            
            # Clean the gripper_id to ensure it doesn't contain spaces or invalid characters
            gripper_id = gripper_id.strip().replace(' ', '_')
            
            # Add joint to its gripper group
            if gripper_id not in gripper_groups:
                gripper_groups[gripper_id] = []
            gripper_groups[gripper_id].append(joint_name)
        
        # Create a subscriber for each gripper group
        for gripper_id, gripper_joints in gripper_groups.items():
            # Create a unique topic name for each gripper - ensure no spaces
            clean_gripper_id = gripper_id.strip().replace(' ', '_')
            
            # Create separate topic names for Float64 and Float32 messages
            float64_topic = f'/ezgripper/{clean_gripper_id}/command_float64'
            float32_topic = f'/ezgripper/{clean_gripper_id}/command'
            
            # Create a subscriber for Float64 messages
            self.subscribers.append(
                self.create_subscription(Float64, float64_topic, 
                                         self.create_callback(gripper_id, gripper_joints), 10)
            )
            self.get_logger().info(f'Created Float64 subscriber for {float64_topic} controlling joints: {gripper_joints}')
            
            # Create a subscriber for Float32 messages (main compatibility topic)
            self.subscribers.append(
                self.create_subscription(Float32, float32_topic, 
                                         self.create_callback(gripper_id, gripper_joints), 10)
            )
            self.get_logger().info(f'Created Float32 subscriber for {float32_topic} controlling joints: {gripper_joints}')
        
        # No default subscriber or grouping - each gripper is completely independent
        
        # Timer to publish joint states
        publish_frequency = 10.0  # Default 10Hz
        self.timer = self.create_timer(1.0/publish_frequency, self.publish_joint_states)

    def _should_invert_joint(self, joint_name):
        """
        Determine whether a joint should be inverted based on its naming pattern.
        This method treats all grippers as independent single units.
        
        The inversion logic is as follows:
        - For all grippers: Invert joints with L1_2 in their name
        
        Args:
            joint_name: The name of the joint to check
            
        Returns:
            bool: True if the joint should be inverted, False otherwise
        """
        # Check if this is a L1_2 joint (finger 2)
        is_l1_2_joint = '_L1_2' in joint_name
        
        # Log the joint name and inversion decision for debugging
        self.get_logger().info(f'Joint {joint_name}: L1_2={is_l1_2_joint}, invert={is_l1_2_joint}')
        
        return is_l1_2_joint
    
    def create_callback(self, prefix, finger_joints):
        def callback(msg):
            # Map the 0-100 range to the actual joint limits (-1.57075 to 0.27)
            # Where 0 is fully closed (0.27 radians) and 100 is fully open (-1.57075 radians)
            JOINT_LOWER_LIMIT = -1.57075  # Fully open position in radians
            JOINT_UPPER_LIMIT = 0.27     # Fully closed position in radians
            
            # Log the command value for debugging
            self.get_logger().info(f'Received command for {prefix}: {msg.data}')
            
            # Normalize the input value (0 to 100) to the joint limits
            # Invert the mapping since 0 should be closed (upper limit) and 100 should be open (lower limit)
            normalized_position = JOINT_UPPER_LIMIT - ((msg.data / 100.0) * (JOINT_UPPER_LIMIT - JOINT_LOWER_LIMIT))
            
            # Log the normalized position for debugging
            self.get_logger().info(f'Normalized position: {normalized_position}')
            
            # Update finger joints for this gripper
            for joint_name in finger_joints:
                # Determine if this joint should be inverted based on its pattern
                should_invert = self._should_invert_joint(joint_name)
                
                if joint_name in self.joint_indexes:
                    index = self.joint_indexes[joint_name]
                    
                    if should_invert:
                        # Invert the position for this joint
                        inverted_position = JOINT_LOWER_LIMIT + (JOINT_UPPER_LIMIT - normalized_position)
                        self.joint_state.position[index] = inverted_position
                        self.get_logger().info(f'Updated {joint_name} position to {inverted_position} (inverted)')
                    else:
                        # Use normal position for this joint
                        self.joint_state.position[index] = normalized_position
                        self.get_logger().info(f'Updated {joint_name} position to {normalized_position} (normal)')
                else:
                    # If the joint isn't in the indexes yet, add it
                    self.joint_state.name.append(joint_name)
                    
                    if should_invert:
                        # Invert the position for this joint
                        inverted_position = JOINT_LOWER_LIMIT + (JOINT_UPPER_LIMIT - normalized_position)
                        self.joint_state.position.append(inverted_position)
                        self.get_logger().info(f'Added {joint_name} with position {inverted_position} (inverted)')
                    else:
                        # Use normal position for this joint
                        self.joint_state.position.append(normalized_position)
                        self.get_logger().info(f'Added {joint_name} with position {normalized_position} (normal)')
                    
                    self.joint_state.velocity.append(0.0)
                    self.joint_state.effort.append(0.0)
                    
                    # Update joint indexes
                    self.joint_indexes = {name: i for i, name in enumerate(self.joint_state.name)}
                    self.get_logger().info(f'Added joint {joint_name} to joint_indexes')
        
        return callback

    def auto_detect_prefix_from_tf(self):
        """Attempt to detect the gripper prefix from the TF tree"""
        try:
            # Wait a bit longer for TF tree to be fully populated
            time.sleep(2.0)
            
            # Get all frames in the TF tree
            frames = self.tf_buffer.all_frames_as_string()
            self.get_logger().info('Scanning TF tree for gripper frames...')
            
            # Look for frames that match the ezgripper pattern
            for line in frames.split('\n'):
                line = line.strip()
                if not line or line.startswith('Frame'): # Skip header lines
                    continue
                    
                if 'ezgripper' in line:
                    # Extract the prefix from the frame name
                    parts = line.strip().split('_')
                    if len(parts) > 1 and 'ezgripper' in parts:
                        # The prefix is everything before 'ezgripper'
                        idx = parts.index('ezgripper')
                        if idx > 0:
                            self.prefix = '_'.join(parts[:idx])
                            self.get_logger().info(f'Auto-detected prefix from TF: {self.prefix}')
                            return
            
            # If we couldn't find a prefix, use the one provided in the parameter
            if not self.prefix:
                self.prefix = 'left_arm'
            self.get_logger().warn(f'Could not auto-detect prefix from TF. Using parameter value: {self.prefix}')
            
        except Exception as e:
            self.get_logger().error(f'Error auto-detecting prefix from TF: {str(e)}')
            if not self.prefix:
                self.prefix = 'left_arm'
            self.get_logger().warn(f'Using parameter value for prefix: {self.prefix}')
    
    def detect_all_gripper_joints_from_tf(self):
        """Detect all gripper joints from the TF tree.
        
        This method finds all palm links in the TF tree and creates the corresponding joint names
        for the knuckle joints based on the palm link prefixes. It works for any gripper configuration
        (single, double, triple, etc.) without special cases.
        
        For each palm link with pattern ${any_prefix}_ezgripper_palm_link, it creates two joint names:
        - ${any_prefix}_ezgripper_knuckle_palm_L1_1
        - ${any_prefix}_ezgripper_knuckle_palm_L1_2
        
        Returns:
            list: List of joint names for all detected grippers
        """
        try:
            # Get all palm links from the TF tree
            palm_links = self.detect_palm_links_from_tf()
            
            if palm_links:
                self.get_logger().info(f'Found {len(palm_links)} palm links: {palm_links}')
            else:
                self.get_logger().warn('No palm links found in TF tree')
            
            # For each palm link, extract the prefix and create joint names
            joint_names = []
            
            # Process each palm link to create joint names
            for palm_link in palm_links:
                # Extract the prefix from the palm link name
                # The pattern is always ${any_prefix}_ezgripper_palm_link
                prefix_match = re.match(r'(.+)_ezgripper_palm_link', palm_link)
                if prefix_match:
                    # Get the prefix (everything before _ezgripper_palm_link)
                    prefix = prefix_match.group(1)
                    
                    # Create knuckle joint names for this gripper
                    # Each gripper has two knuckle joints: L1_1 and L1_2
                    knuckle_joint_1 = f'{prefix}_ezgripper_knuckle_palm_L1_1'
                    knuckle_joint_2 = f'{prefix}_ezgripper_knuckle_palm_L1_2'
                    
                    # Add the joints to our list
                    joint_names.append(knuckle_joint_1)
                    joint_names.append(knuckle_joint_2)
                    
                    self.get_logger().info(f'Created joint names for gripper with prefix: {prefix}')
            
            # If we didn't find any palm links, fall back to default
            if not palm_links:
                self.get_logger().warn('No palm links found in TF tree. Using default prefix.')
                joint_names.append(f'{self.prefix}_ezgripper_knuckle_palm_L1_1')
                joint_names.append(f'{self.prefix}_ezgripper_knuckle_palm_L1_2')
            
            # Ensure we don't have duplicate joint names
            unique_joint_names = list(set(joint_names))
            self.get_logger().info(f'Final joint names: {unique_joint_names}')
            return unique_joint_names
            
        except Exception as e:
            self.get_logger().error(f'Error detecting gripper joints: {str(e)}')
            # Create default joint names as a fallback
            joint_names = [
                f'{self.prefix}_ezgripper_knuckle_palm_L1_1',
                f'{self.prefix}_ezgripper_knuckle_palm_L1_2'
            ]
            self.get_logger().info(f'Using fallback joint names due to error: {joint_names}')
            return joint_names
    
    def detect_palm_links_from_tf(self):
        """Detect palm links from the TF tree.
        
        This method finds all palm links in the TF tree with pattern ${any_prefix}_ezgripper_palm_link.
        It works for any gripper configuration (single, double, triple, etc.) without filtering.
        
        Returns:
            list: List of palm link names
        """
        try:
            # Get all frames in the TF tree
            frames = self.tf_buffer.all_frames_as_string()
            
            # Look for frames that match the palm link pattern
            palm_links = []
            for line in frames.split('\n'):
                line = line.strip()
                if not line or line.startswith('Frame'): # Skip header lines
                    continue
                
                # Look for any frame with 'ezgripper_palm_link' in its name
                if 'ezgripper_palm_link' in line:
                    # Extract the frame name
                    match = re.search(r'Frame ([^ ]+) exists', line)
                    if match:
                        frame_name = match.group(1)
                        # Add all palm links without filtering
                        palm_links.append(frame_name)
                        self.get_logger().info(f'Detected palm link from TF: {frame_name}')
            
            if palm_links:
                self.get_logger().info(f'Found {len(palm_links)} palm links in TF tree: {palm_links}')
            else:
                self.get_logger().warn('No palm links found in TF tree. Make sure the URDF is loaded correctly.')
                
            return palm_links
        except Exception as e:
            self.get_logger().error(f'Error detecting palm links from TF: {str(e)}')
            return []
    
    def check_frame_exists(self, frame_name):
        """Check if a frame exists in the TF tree
        
        Args:
            frame_name: The name of the frame to check
            
        Returns:
            bool: True if the frame exists, False otherwise
        """
        try:
            frames = self.tf_buffer.all_frames_as_string()
            for line in frames.split('\n'):
                if f'Frame {frame_name} exists' in line:
                    return True
            return False
        except Exception as e:
            self.get_logger().error(f'Error checking if frame exists: {str(e)}')
            return False
            
    def detect_joint_names_from_tf(self):
        """Attempt to detect joint names from the TF tree"""
        try:
            # Get all frames in the TF tree
            frames = self.tf_buffer.all_frames_as_string()
            
            # Look for frames that match joint patterns
            joint_names = []
            for line in frames.split('\n'):
                line = line.strip()
                if not line or line.startswith('Frame'): # Skip header lines
                    continue
                
                # Look for gripper joint frames
                if 'knuckle_palm' in line and 'ezgripper' in line:
                    joint_name = line
                    
                    # Check if this joint matches our prefix (if one was provided)
                    if self.prefix and not joint_name.startswith(self.prefix):
                        self.get_logger().debug(f'Skipping joint {joint_name} as it does not match prefix {self.prefix}')
                        continue
                    
                    joint_names.append(joint_name)
                    
                    self.get_logger().info(f'Detected joint from TF: {joint_name}')
            
            # If we didn't find any joints but have a prefix, try again without prefix filtering
            # This is a fallback in case the TF frames don't match our expected pattern
            if not joint_names and self.prefix:
                self.get_logger().warn(f'No joints found with prefix {self.prefix}. Trying without prefix filtering.')
                for line in frames.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('Frame'): # Skip header lines
                        continue
                    
                    # Look for gripper joint frames
                    if 'knuckle_palm' in line and 'ezgripper' in line:
                        joint_name = line
                        joint_names.append(joint_name)
                        self.get_logger().info(f'Detected joint from TF (without prefix filtering): {joint_name}')
            
            # Return the detected joint names
            
            return joint_names
        except Exception as e:
            self.get_logger().error(f'Error detecting joint names from TF: {str(e)}')
            return []
    
    def publish_joint_states(self):
        # Update timestamp
        self.joint_state.header.stamp = self.get_clock().now().to_msg()
        
        # Check if we have any joint names in the joint state message
        if not self.joint_state.name:
            self.get_logger().warn('No joint names in joint state message. Creating joint names based on URDF conventions.')
            
            # Define default position values
            JOINT_LOWER_LIMIT = -1.57075  # Fully open position in radians
            JOINT_UPPER_LIMIT = 0.27     # Fully closed position in radians
            DEFAULT_POSITION = 0.0       # Neutral position
            
            # Initialize joint state arrays
            self.joint_state.name = []
            self.joint_state.position = []
            self.joint_state.velocity = []
            self.joint_state.effort = []
            
            # Determine if we're dealing with a single or triple gripper based on the prefix parameter
            # The prefix parameter is passed from the launch file and corresponds to the URDF prefix
            self.get_logger().info(f'Using prefix from parameter: {self.prefix}')
            
            # Based on the TF tree, we need to create joint names for all grippers in the triple configuration
            # For the triple gripper, we have these joints:
            # Base gripper: ${prefix}_ezgripper_knuckle_palm_L1_1, ${prefix}_ezgripper_knuckle_palm_L1_2, ${prefix}_ezgripper_knuckle_palm_L1_3
            # Gripper 1: ${prefix}_1_ezgripper_knuckle_palm_L1_1, ${prefix}_1_ezgripper_knuckle_palm_L1_2, ${prefix}_1_ezgripper_knuckle_palm_L1_3
            # Gripper 2: ${prefix}_2_ezgripper_knuckle_palm_L1_1, ${prefix}_2_ezgripper_knuckle_palm_L1_2, ${prefix}_2_ezgripper_knuckle_palm_L1_3
            # Gripper 3: ${prefix}_3_ezgripper_knuckle_palm_L1_1, ${prefix}_3_ezgripper_knuckle_palm_L1_2, ${prefix}_3_ezgripper_knuckle_palm_L1_3
            
            # Create all joint names for the triple gripper configuration
            all_joints = []
            
            # Base gripper joints
            base_joints = [
                f'{self.prefix}_ezgripper_knuckle_palm_L1_1',
                f'{self.prefix}_ezgripper_knuckle_palm_L1_2',
                f'{self.prefix}_ezgripper_knuckle_palm_L1_3'
            ]
            all_joints.extend(base_joints)
            
            # Numbered gripper joints (1, 2, 3)
            for i in range(1, 4):
                numbered_joints = [
                    f'{self.prefix}_{i}_ezgripper_knuckle_palm_L1_1',
                    f'{self.prefix}_{i}_ezgripper_knuckle_palm_L1_2',
                    f'{self.prefix}_{i}_ezgripper_knuckle_palm_L1_3'
                ]
                all_joints.extend(numbered_joints)
            
            # Add all joints to the joint state message
            for joint in all_joints:
                self.joint_state.name.append(joint)
                self.joint_state.position.append(DEFAULT_POSITION)
                self.joint_state.velocity.append(0.0)
                self.joint_state.effort.append(0.0)
            
            self.get_logger().info(f'Created joint names based on URDF: {all_joints}')
            
            # Create subscribers for each gripper
            # Base gripper
            topic_name = f'/ezgripper/{self.prefix}/command'
            self.subscribers.append(
                self.create_subscription(Float32, topic_name, 
                                      self.create_callback(self.prefix, base_joints), 10)
            )
            self.get_logger().info(f'Created subscriber for {topic_name} controlling joints: {base_joints}')
            
            # Also create Float64 topic for compatibility
            topic_name_float64 = f'/ezgripper/{self.prefix}/command_float64'
            self.subscribers.append(
                self.create_subscription(Float64, topic_name_float64,
                                      self.create_callback(self.prefix, base_joints), 10)
            )
            self.get_logger().info(f'Created Float64 subscriber for {topic_name_float64}')
            
            # Numbered grippers (1, 2, 3)
            for i in range(1, 4):
                numbered_prefix = f'{self.prefix}_{i}'
                numbered_joints = [
                    f'{numbered_prefix}_ezgripper_knuckle_palm_L1_1',
                    f'{numbered_prefix}_ezgripper_knuckle_palm_L1_2',
                    f'{numbered_prefix}_ezgripper_knuckle_palm_L1_3'
                ]
                
                # Create subscribers for this numbered gripper
                topic_name = f'/ezgripper/{numbered_prefix}/command'
                self.subscribers.append(
                    self.create_subscription(Float32, topic_name, 
                                          self.create_callback(numbered_prefix, numbered_joints), 10)
                )
                self.get_logger().info(f'Created subscriber for {topic_name} controlling joints: {numbered_joints}')
                
                # Also create Float64 topic for compatibility
                topic_name_float64 = f'/ezgripper/{numbered_prefix}/command_float64'
                self.subscribers.append(
                    self.create_subscription(Float64, topic_name_float64,
                                          self.create_callback(numbered_prefix, numbered_joints), 10)
                )
                self.get_logger().info(f'Created Float64 subscriber for {topic_name_float64}')
            
            # Update joint indexes
            self.joint_indexes = {name: i for i, name in enumerate(self.joint_state.name)}
            self.get_logger().info(f'Final joint names: {self.joint_state.name}')
        
        # Publish the joint state with the correct joint names to component-level topic only
        # Do NOT publish to global joint_states - that should be handled by the launch hierarchy
        self.publisher.publish(self.joint_state)
        
        self.get_logger().debug(f'Published joint states with names: {self.joint_state.name}')

def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = GripperJointPublisher()
        rclpy.spin(node)
    except Exception as e:
        print(f'Exception in node: {str(e)}')
    finally:
        # Destroy the node explicitly
        rclpy.shutdown()

if __name__ == '__main__':
    main()
