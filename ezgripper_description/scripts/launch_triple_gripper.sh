#!/bin/bash
# Launch Triple Gripper Script
# This script directly launches the triple gripper using the approach that worked in our test script

# Source ROS workspace
source /home/sake/linorobot2_ws/install/setup.bash

# Set variables
PACKAGE_PATH=$(ros2 pkg prefix ezgripper_description)
URDF_PATH="${PACKAGE_PATH}/share/ezgripper_description/urdf/ezgripper_triple_with_mount_standalone.urdf.xacro"
PREFIX="gripper"

# Process XACRO file and save to temporary file
TEMP_URDF="/tmp/ezgripper_triple.urdf"
TEMP_YAML="/tmp/ezgripper_params.yaml"
echo "Processing XACRO file: ${URDF_PATH}"
xacro "${URDF_PATH}" "prefix:=${PREFIX}" > "${TEMP_URDF}"

# Create a parameter file for robot_description
echo "Creating parameter file"
echo "robot_state_publisher:" > "${TEMP_YAML}"
echo "  ros__parameters:" >> "${TEMP_YAML}"
echo "    robot_description: |
$(cat ${TEMP_URDF} | sed 's/^/      /')" >> "${TEMP_YAML}"
echo "    use_sim_time: false" >> "${TEMP_YAML}"

# Launch robot_state_publisher with the parameter file
echo "Launching robot_state_publisher with parameter file"
ros2 run robot_state_publisher robot_state_publisher --ros-args --params-file "${TEMP_YAML}" &
RSP_PID=$!

# Launch static transform publisher for base frames
echo "Launching static transform publisher for base frames"
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 world gripper_1_ezgripper_palm_link &
STF1_PID=$!
ros2 run tf2_ros static_transform_publisher 0 0.1 0 0 0 0 world gripper_2_ezgripper_palm_link &
STF2_PID=$!
ros2 run tf2_ros static_transform_publisher 0 0.2 0 0 0 0 world gripper_3_ezgripper_palm_link &
STF3_PID=$!

# Launch joint state publisher
echo "Launching joint state publisher"
ros2 run ezgripper_description gripper_joint_publisher.py --ros-args -p use_sim_time:=false -p enable_hardware:=false -p namespace:=ezgripper -p prefix:=${PREFIX} &
JSP_PID=$!

# Launch RViz
echo "Launching RViz"
ros2 run rviz2 rviz2 -d "${PACKAGE_PATH}/share/ezgripper_description/rviz/urdf.rviz" &
RVIZ_PID=$!

# Wait for RViz to exit
echo "Waiting for RViz to exit"
wait ${RVIZ_PID}

# Clean up
echo "Cleaning up"
kill ${RSP_PID} ${JSP_PID} ${STF1_PID} ${STF2_PID} ${STF3_PID}
rm "${TEMP_URDF}" "${TEMP_YAML}"

echo "Done"
