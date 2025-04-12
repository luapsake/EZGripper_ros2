#!/usr/bin/env python3
"""
Cleanup script for EZGripper processes
This script finds and terminates any running EZGripper processes to prevent
duplicate instances when launching the gripper multiple times.
"""
import os
import signal
import subprocess
import rclpy
from rclpy.node import Node

class EZGripperProcessCleaner(Node):
    def __init__(self):
        super().__init__('ezgripper_process_cleaner')
        self.get_logger().info('Cleaning up EZGripper processes...')
        self.cleanup_processes()
        
    def cleanup_processes(self):
        # Find all gripper_joint_publisher and gripper_static_tf_publisher processes
        try:
            # Use absolute paths for commands
            result = subprocess.run(
                ['/usr/bin/pgrep', '-f', '(gripper_joint_publisher|gripper_static_tf_publisher)'],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                self.get_logger().info(f'Found {len(pids)} EZGripper processes to clean up')
                
                # Get our own PID to avoid killing ourselves
                own_pid = os.getpid()
                
                # Kill each process
                for pid_str in pids:
                    try:
                        pid = int(pid_str)
                        # Don't kill our own process
                        if pid != own_pid:
                            self.get_logger().info(f'Terminating process {pid}')
                            os.kill(pid, signal.SIGTERM)
                    except (ValueError, ProcessLookupError) as e:
                        self.get_logger().warning(f'Error terminating process {pid_str}: {e}')
            else:
                self.get_logger().info('No EZGripper processes found to clean up')
                
        except Exception as e:
            self.get_logger().error(f'Error cleaning up processes: {e}')
            
        self.get_logger().info('EZGripper process cleanup completed')

def main(args=None):
    rclpy.init(args=args)
    cleaner = EZGripperProcessCleaner()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
