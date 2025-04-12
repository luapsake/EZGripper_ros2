#!/usr/bin/env python3
"""
Cleanup script for EZGripper processes
This script finds and terminates any lingering EZGripper processes
to ensure clean shutdown of the system.
"""

import os
import signal
import subprocess
import sys
import rclpy
from rclpy.node import Node


class EZGripperCleanupNode(Node):
    """Node to cleanup EZGripper processes"""

    def __init__(self):
        super().__init__('ezgripper_cleanup')
        self.get_logger().info('EZGripper Cleanup Node started')
        self.cleanup_processes()

    def cleanup_processes(self):
        """Find and terminate EZGripper processes"""
        self.get_logger().info('Cleaning up EZGripper processes...')
        
        # Get our own PID to avoid killing ourselves
        own_pid = os.getpid()
        
        # Get our parent PID (the launch process)
        parent_pid = os.getppid()
        self.get_logger().info(f'Our PID: {own_pid}, Parent PID: {parent_pid}')
        
        # Get all child processes of our parent (siblings of this process)
        # These are part of the current launch and should not be killed
        siblings = []
        try:
            ps_cmd = f"/usr/bin/ps --ppid {parent_pid} -o pid="
            result = subprocess.run(ps_cmd, shell=True, text=True, capture_output=True)
            if result.stdout.strip():
                for line in result.stdout.splitlines():
                    if line.strip():
                        try:
                            sibling_pid = int(line.strip())
                            siblings.append(sibling_pid)
                        except ValueError:
                            pass
            self.get_logger().info(f'Sibling processes to preserve: {siblings}')
        except subprocess.SubprocessError as e:
            self.get_logger().error(f'Error getting sibling processes: {e}')
        
        # List of process patterns to look for
        process_patterns = [
            'gripper_joint_publisher',
            'gripper_static_',
            'ezgripper_'
        ]
        
        for pattern in process_patterns:
            self.get_logger().info(f'Looking for processes matching: {pattern}')
            try:
                # Find processes matching the pattern
                ps_cmd = f"/usr/bin/ps aux | /usr/bin/grep {pattern} | /usr/bin/grep -v grep | /usr/bin/grep -v cleanup"
                result = subprocess.run(ps_cmd, shell=True, text=True, capture_output=True)
                
                if not result.stdout.strip():
                    self.get_logger().info(f'No processes found matching {pattern}')
                    continue
                    
                # Process each line of output
                for line in result.stdout.splitlines():
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            pid = parts[1]
                            try:
                                pid = int(pid)
                                
                                # Skip our own process and siblings (current launch processes)
                                if pid == own_pid or pid in siblings or pid == parent_pid:
                                    self.get_logger().info(f'Skipping process {pid} as it appears to be part of the current launch')
                                    continue
                                    
                                self.get_logger().info(f'Terminating process {pid}: {line}')
                                os.kill(pid, signal.SIGINT)
                                # Give the process a moment to terminate gracefully
                                try:
                                    subprocess.run(f"sleep 0.5 && kill -0 {pid} 2>/dev/null && kill -9 {pid}", 
                                                  shell=True, check=False)
                                except subprocess.SubprocessError:
                                    pass
                            except (ValueError, ProcessLookupError) as e:
                                self.get_logger().error(f'Error terminating process: {e}')
                        else:
                            self.get_logger().warning(f'Could not parse process line: {line}')
                
            except subprocess.SubprocessError as e:
                self.get_logger().error(f'Error finding processes: {e}')
        
        # Final check for any remaining processes
        self.get_logger().info('Checking for any remaining EZGripper processes...')
        try:
            check_cmd = "/usr/bin/ps aux | /usr/bin/grep -E 'gripper_static_|gripper_joint_publisher|ezgripper_' | /usr/bin/grep -v grep | /usr/bin/grep -v cleanup"
            result = subprocess.run(check_cmd, shell=True, text=True, capture_output=True)
            
            if result.stdout.strip():
                self.get_logger().info('Some EZGripper processes are still running. Forcibly terminating them...')
                # Process each remaining process individually to avoid killing siblings
                for line in result.stdout.splitlines():
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                                
                                # Skip our own process and siblings (current launch processes)
                                if pid == own_pid or pid in siblings or pid == parent_pid:
                                    self.get_logger().info(f'Skipping process {pid} as it appears to be part of the current launch')
                                    continue
                                    
                                self.get_logger().info(f'Force killing process {pid}')
                                # Use SIGKILL for stubborn processes
                                os.kill(pid, signal.SIGKILL)
                            except (ValueError, ProcessLookupError) as e:
                                self.get_logger().error(f'Error killing process: {e}')
            else:
                self.get_logger().info('All EZGripper processes have been terminated')
        
        except subprocess.SubprocessError as e:
            self.get_logger().error(f'Error checking for remaining processes: {e}')


def cleanup_without_ros():
    """Direct process cleanup without relying on ROS"""
    print("Performing direct process cleanup...")
    
    # Get our own PID to avoid killing ourselves
    own_pid = os.getpid()
    
    # Get our parent PID (the launch process)
    parent_pid = os.getppid()
    print(f'Our PID: {own_pid}, Parent PID: {parent_pid}')
    
    # Get all child processes of our parent (siblings of this process)
    # These are part of the current launch and should not be killed
    siblings = []
    try:
        ps_cmd = f"/usr/bin/ps --ppid {parent_pid} -o pid="
        result = subprocess.run(ps_cmd, shell=True, text=True, capture_output=True)
        if result.stdout.strip():
            for line in result.stdout.splitlines():
                if line.strip():
                    try:
                        sibling_pid = int(line.strip())
                        siblings.append(sibling_pid)
                    except ValueError:
                        pass
        print(f'Sibling processes to preserve: {siblings}')
    except subprocess.SubprocessError as e:
        print(f'Error getting sibling processes: {e}')
    
    # List of process patterns to look for
    process_patterns = [
        'gripper_joint_publisher',
        'gripper_static_',
        'ezgripper_'
    ]
    
    for pattern in process_patterns:
        print(f"Looking for processes matching: {pattern}")
        try:
            # Find processes matching the pattern
            ps_cmd = f"/usr/bin/ps aux | /usr/bin/grep {pattern} | /usr/bin/grep -v grep | /usr/bin/grep -v cleanup"
            result = subprocess.run(ps_cmd, shell=True, text=True, capture_output=True)
            
            if not result.stdout.strip():
                print(f"No processes found matching {pattern}")
                continue
                
            # Process each line of output
            for line in result.stdout.splitlines():
                if line.strip():
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        try:
                            pid = int(pid)
                            
                            # Skip our own process and siblings (current launch processes)
                            if pid == own_pid or pid in siblings or pid == parent_pid:
                                print(f"Skipping process {pid} as it appears to be part of the current launch")
                                continue
                                
                            print(f"Terminating process {pid}: {line}")
                            os.kill(pid, signal.SIGINT)
                            # Give the process a moment to terminate gracefully
                            try:
                                subprocess.run(f"sleep 0.5 && kill -0 {pid} 2>/dev/null && kill -9 {pid}", 
                                              shell=True, check=False)
                            except subprocess.SubprocessError:
                                pass
                        except (ValueError, ProcessLookupError) as e:
                            print(f"Error terminating process: {e}")
                    else:
                        print(f"Could not parse process line: {line}")
            
        except subprocess.SubprocessError as e:
            print(f"Error finding processes: {e}")
    
    # Check if any EZGripper processes are still running
    print("Checking for any remaining EZGripper processes...")
    try:
        check_cmd = "/usr/bin/ps aux | /usr/bin/grep -E 'gripper_static_|gripper_joint_publisher|ezgripper_' | /usr/bin/grep -v grep | /usr/bin/grep -v cleanup"
        result = subprocess.run(check_cmd, shell=True, text=True, capture_output=True)
        
        if result.stdout.strip():
            print("Some EZGripper processes are still running. Forcibly terminating them...")
            # Process each remaining process individually to avoid killing siblings
            for line in result.stdout.splitlines():
                if line.strip():
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            
                            # Skip our own process and siblings (current launch processes)
                            if pid == own_pid or pid in siblings or pid == parent_pid:
                                print(f"Skipping process {pid} as it appears to be part of the current launch")
                                continue
                                
                            print(f"Force killing process {pid}")
                            # Use SIGKILL for stubborn processes
                            os.kill(pid, signal.SIGKILL)
                        except (ValueError, ProcessLookupError) as e:
                            print(f"Error killing process: {e}")
        else:
            print("All EZGripper processes have been terminated")
    
    except subprocess.SubprocessError as e:
        print(f"Error checking for remaining processes: {e}")


def main(args=None):
    """Main function"""
    try:
        # Try to initialize ROS
        rclpy.init(args=args)
        node = EZGripperCleanupNode()
        # Just spin once to process the cleanup
        rclpy.spin_once(node, timeout_sec=1.0)
        node.destroy_node()
        rclpy.shutdown()
    except Exception as e:
        print(f"Error initializing ROS: {e}")
        print("Falling back to direct process cleanup...")
        cleanup_without_ros()


if __name__ == '__main__':
    main()
