#!/usr/bin/env python3
"""
Test script for Triple EZGripper

This script directly processes the XACRO file and launches the triple gripper
to debug any issues with the XACRO processing.
"""
import os
import subprocess
import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
import xml.etree.ElementTree as ET
from std_msgs.msg import Float32
import tf2_ros
import time

class TripleGripperTester(Node):
    def __init__(self):
        super().__init__('triple_gripper_tester')
        
        # Get package directories
        self.pkg_dir = get_package_share_directory('ezgripper_description')
        
        # Process XACRO file
        self.get_logger().info('Processing XACRO file...')
        urdf_file = os.path.join(self.pkg_dir, 'urdf', 'ezgripper_triple_with_mount_standalone.urdf.xacro')
        
        # Use subprocess to process the XACRO file
        try:
            cmd = ['xacro', urdf_file, 'prefix:=gripper']
            self.get_logger().info(f'Running command: {" ".join(cmd)}')
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.get_logger().error(f'Error processing XACRO file: {result.stderr}')
                return
            
            # Save the processed URDF to a temporary file
            processed_urdf = result.stdout
            self.get_logger().info('XACRO processing successful')
            
            # Create TF buffer and listener
            self.tf_buffer = tf2_ros.Buffer()
            self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
            
            # Wait for TF data
            self.get_logger().info('Waiting for TF data...')
            self.timer = self.create_timer(1.0, self.check_tf_tree)
            
        except Exception as e:
            self.get_logger().error(f'Error: {str(e)}')
    
    def check_tf_tree(self):
        """Check the TF tree for gripper frames"""
        try:
            # Get all frames
            frames = self.tf_buffer.all_frames_as_string()
            self.get_logger().info(f'TF Tree:\n{frames}')
            
            # Look for palm links
            palm_links = []
            for line in frames.split('\n'):
                if 'ezgripper_palm_link' in line:
                    palm_links.append(line.strip())
            
            if palm_links:
                self.get_logger().info(f'Found palm links: {palm_links}')
            else:
                self.get_logger().warning('No palm links found in TF tree')
                
        except Exception as e:
            self.get_logger().error(f'Error checking TF tree: {str(e)}')

def main():
    rclpy.init()
    node = TripleGripperTester()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
