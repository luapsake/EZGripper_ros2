#!/usr/bin/env python3
"""
Test script for EZGripper launch files
This script runs a series of tests on the EZGripper launch files,
collects debug information, and saves the results to separate files.
"""

import os
import sys
import time
import subprocess
import signal
import datetime
from pathlib import Path

# Define the tests to run
TESTS = [
    {
        "name": "single_description",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_single_description.launch.py",
        "description": "Single EZGripper Description Launch File"
    },
    {
        "name": "double_description",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_double_description.launch.py",
        "description": "Double EZGripper Description Launch File"
    },
    {
        "name": "triple_description",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_triple_description.launch.py",
        "description": "Triple EZGripper Description Launch File"
    },
    {
        "name": "single_integration",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_single_integration.launch.py",
        "description": "Single EZGripper Integration Launch File"
    },
    {
        "name": "double_integration",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_double_integration.launch.py",
        "description": "Double EZGripper Integration Launch File"
    },
    {
        "name": "triple_integration",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_triple_integration.launch.py",
        "description": "Triple EZGripper Integration Launch File"
    },
    {
        "name": "single_standalone",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_single_standalone.launch.py",
        "description": "Single EZGripper Standalone Launch File"
    },
    {
        "name": "double_standalone",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_double_standalone.launch.py",
        "description": "Double EZGripper Standalone Launch File"
    },
    {
        "name": "triple_standalone",
        "command": "/opt/ros/humble/bin/ros2 launch ezgripper_description ezgripper_triple_standalone.launch.py",
        "description": "Triple EZGripper Standalone Launch File"
    }
]

def run_debug_commands(output_file):
    """Run debug commands and write output to file"""
    # Define ROS2 executable paths
    ros2_bin = "/opt/ros/humble/bin/ros2"
    timeout_bin = "/usr/bin/timeout"
    ps_bin = "/usr/bin/ps"
    grep_bin = "/usr/bin/grep"
    
    debug_commands = [
        ("Running Processes (ps -a)", f"{ps_bin} -a"),
        ("ROS2 Process List (grep python)", f"{ps_bin} aux | {grep_bin} python | {grep_bin} -v grep"),
        ("ROS2 Node List", f"{ros2_bin} node list"),
        ("ROS2 Topic List", f"{ros2_bin} topic list"),
        ("ROS2 Parameter List", f"{ros2_bin} param list"),
        ("Robot Prefix Parameter Value", f"{ros2_bin} param get /robot_state_publisher prefix 2>/dev/null || echo \"Parameter not found\""),
        ("Node Info for Joint State Publisher", f"{ros2_bin} node info /ezgripper/gripper_joint_publisher 2>/dev/null || echo \"Node not found or not running\""),
        ("Node Info for Robot State Publisher", f"{ros2_bin} node info /ezgripper/robot_state_publisher 2>/dev/null || echo \"Node not found or not running\""),
        ("Checking EZGripper Joint State Topic", f"{timeout_bin} 3 {ros2_bin} topic echo --once /ezgripper/joint_states 2>/dev/null || echo \"No messages received\""),
        ("Checking TF Tree", f"{timeout_bin} 3 {ros2_bin} run tf2_tools view_frames.py 2>/dev/null || echo \"Unable to generate TF tree\""),
        ("Checking Joint States Topic", f"{timeout_bin} 3 {ros2_bin} topic echo --once /joint_states 2>/dev/null || echo \"No messages received\"")
    ]
    
    for title, cmd in debug_commands:
        output_file.write(f"\n=== {title} ===\n")
        try:
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=10)
            output_file.write(result.stdout)
            if result.stderr:
                output_file.write(f"ERROR: {result.stderr}\n")
        except subprocess.TimeoutExpired:
            output_file.write("Command timed out after 10 seconds\n")
        except Exception as e:
            output_file.write(f"Error executing command: {e}\n")
        output_file.write("\n")

def run_test(test, results_dir):
    """Run a single test and collect results"""
    test_name = test["name"]
    test_cmd = test["command"]
    test_desc = test["description"]
    
    print(f"\n\n{'='*80}")
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] TEST {test_name} ({test_desc})")
    print(f"{'='*80}")
    
    # Create output file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_path = os.path.join(results_dir, f"{test_name}_{timestamp}.txt")
    
    with open(output_file_path, 'w') as output_file:
        # Write test header
        output_file.write(f"TEST: {test_desc}\n")
        output_file.write(f"COMMAND: {test_cmd}\n")
        output_file.write(f"TIMESTAMP: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output_file.write(f"{'='*80}\n\n")
        
        # Start the launch file process
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ▶️ Starting {test_name}...")
            launch_process = subprocess.Popen(
                test_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                preexec_fn=os.setsid
            )
            
            # Wait for nodes to start up with progress indicator
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⏳ Waiting for nodes to start up...")
            for i in range(10):
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush()
            print(" Done!")
            
            # Collect debug information
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔍 Collecting debug information...")
            run_debug_commands(output_file)
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Debug information collected")
            
            # Terminate the launch process
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🛑 Terminating {test_name}...")
            os.killpg(os.getpgid(launch_process.pid), signal.SIGINT)
            
            # Wait for process to terminate with progress indicator
            try:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⏳ Waiting for process to terminate...")
                for i in range(10):
                    if launch_process.poll() is not None:
                        print(" Process terminated!")
                        break
                    time.sleep(1)
                    sys.stdout.write(".")
                    sys.stdout.flush()
                else:
                    print(" Timeout!")
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Process didn't terminate, forcing kill...")
                    os.killpg(os.getpgid(launch_process.pid), signal.SIGKILL)
            except subprocess.TimeoutExpired:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Process didn't terminate, forcing kill...")
                os.killpg(os.getpgid(launch_process.pid), signal.SIGKILL)
            
            # Wait for cleanup with progress indicator
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🧹 Waiting for cleanup...")
            for i in range(5):
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush()
            print(" Done!")
            
            # Check for any lingering processes
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔍 Checking for lingering processes...")
            output_file.write("\n=== Checking for Lingering Processes ===\n")
            ps_cmd = "/usr/bin/ps aux | /usr/bin/grep ezgripper | /usr/bin/grep -v grep"
            ps_result = subprocess.run(ps_cmd, shell=True, text=True, capture_output=True)
            if ps_result.stdout.strip():
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Found lingering processes, running cleanup script...")
                output_file.write("WARNING: Found lingering EZGripper processes:\n")
                output_file.write(ps_result.stdout)
                
                # Run cleanup script
                output_file.write("\n=== Running Cleanup Script ===\n")
                cleanup_cmd = "/opt/ros/humble/bin/ros2 run ezgripper_description cleanup_ezgripper_processes.py"
                cleanup_result = subprocess.run(cleanup_cmd, shell=True, text=True, capture_output=True)
                output_file.write(cleanup_result.stdout)
                if cleanup_result.stderr:
                    output_file.write(f"ERROR: {cleanup_result.stderr}\n")
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Cleanup completed")
            else:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ No lingering processes found")
                output_file.write("No lingering EZGripper processes found.\n")
            
        except Exception as e:
            output_file.write(f"\nERROR: Test failed with exception: {e}\n")
        
        # Write test footer
        output_file.write(f"\n{'='*80}\n")
        output_file.write(f"TEST COMPLETED: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"Test results saved to: {output_file_path}")
    return output_file_path

def main():
    # Create results directory
    results_dir = os.path.join(os.path.expanduser("~"), "ezgripper_test_results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Print header
    print("\n" + "="*80)
    print("🤖 EZGripper Launch File Test Suite")
    print(f"🕒 Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Results will be saved to: {results_dir}")
    print(f"🧪 Running {len(TESTS)} tests")
    print("="*80 + "\n")
    
    # Run all tests
    test_results = []
    for i, test in enumerate(TESTS):
        try:
            print(f"\n[{i+1}/{len(TESTS)}] Running test: {test['name']}")
            result_file = run_test(test, results_dir)
            test_results.append((test["name"], "✅ COMPLETED", result_file))
        except Exception as e:
            print(f"\n❌ ERROR: Test {test['name']} failed: {e}")
            test_results.append((test["name"], f"❌ FAILED: {e}", None))
    
    # Print summary
    print("\n\n")
    print("="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    successful_tests = sum(1 for _, status, _ in test_results if "COMPLETED" in status)
    print(f"Total tests: {len(TESTS)} | Successful: {successful_tests} | Failed: {len(TESTS) - successful_tests}")
    print("-"*80)
    for name, status, result_file in test_results:
        result_path = os.path.basename(result_file) if result_file else "N/A"
        print(f"{name:25} | {status:15} | {result_path}")
    print("="*80)
    print(f"📁 All test results saved to: {results_dir}")
    print(f"🕒 Finished at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
