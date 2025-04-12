#!/bin/bash

# Default parameters
PREFIX="left_arm"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --prefix=*)
      PREFIX="${1#*=}"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

echo "=== EZGripper Debug Tool ==="
echo "This script checks the status of EZGripper components and connections"
echo "Using prefix: ${PREFIX}"
echo ""

echo "=== Running Processes (ps -a) ==="
ps -a | grep -E 'python|ezgripper|ros'
echo ""

echo "=== ROS2 Node List ==="
ros2 node list | grep -E 'ezgripper|joint|robot_state'
echo ""

echo "=== ROS2 Topic List (Gripper Related) ==="
ros2 topic list | grep -E 'ezgripper|joint|tf'
echo ""

echo "=== Checking EZGripper Joint State Topic ==="
echo "--- /ezgripper/joint_states (full message) ---"
timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null || echo "No messages received"
echo ""

echo "=== Checking Aggregated Joint State Topic ==="
echo "--- /joint_states (filtered for ezgripper) ---"
timeout 3 ros2 topic echo --once /joint_states 2>/dev/null | grep -A 20 -B 2 "ezgripper" || echo "No EZGripper joints found in joint_states"
echo ""

echo "=== Joint States Publishing Rate ==="
timeout 5 ros2 topic hz /ezgripper/joint_states --window 5 2>/dev/null || echo "No messages received"
echo ""

echo "=== Analyzing Joint Names and Positions ==="
JOINT_DATA=$(timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null)
echo "$JOINT_DATA" > /tmp/joint_data.txt

echo "Joint Names:"
grep -A 50 "name:" /tmp/joint_data.txt | grep -v "name:" | grep -v "position:" | grep -v "^$"

echo "\nJoint Positions:"
grep -A 50 "position:" /tmp/joint_data.txt | grep -v "position:" | grep -v "velocity:" | grep -v "^$"

echo "\nAnalyzing L1_1 vs L1_2 joints..."
L1_1_JOINTS=$(grep -A 50 "name:" /tmp/joint_data.txt | grep -v "name:" | grep "L1_1")
L1_2_JOINTS=$(grep -A 50 "name:" /tmp/joint_data.txt | grep -v "name:" | grep "L1_2")

echo "L1_1 Joints: $L1_1_JOINTS"
echo "L1_2 Joints: $L1_2_JOINTS"

# Extract joint prefixes for analysis
echo "\nExtracting joint prefixes for analysis..."
JOINT_PREFIXES=$(grep -A 50 "name:" /tmp/joint_data.txt | grep -v "name:" | grep -v "position:" | grep -v "^$" | grep "ezgripper_knuckle_palm" | sed -E 's/- (.+)_ezgripper_knuckle_palm.+/\1/g' | sort | uniq)
echo "Detected joint prefixes: $JOINT_PREFIXES"

# Check for all L1_N joints (N-gripper configuration)
echo "\nAnalyzing L1_N joints in joint states:"
L1_JOINT_NUMBERS=$(grep -A 50 "name:" /tmp/joint_data.txt | grep -v "name:" | grep -v "^$" | grep -o "L1_[0-9]\+" | sed 's/L1_//' | sort -n | uniq)

if [ -n "$L1_JOINT_NUMBERS" ]; then
    echo "✓ Found the following L1_N joints:"
    for NUM in $L1_JOINT_NUMBERS; do
        L1_N_JOINTS=$(grep -A 50 "name:" /tmp/joint_data.txt | grep -v "name:" | grep -v "^$" | grep "L1_$NUM")
        JOINT_COUNT=$(echo "$L1_N_JOINTS" | grep -v "^$" | wc -l)
        echo "  L1_$NUM: $JOINT_COUNT joints"
    done
    
    # Count total number of unique L1_N patterns
    L1_PATTERN_COUNT=$(echo "$L1_JOINT_NUMBERS" | wc -w)
    echo "\nTotal number of unique L1_N patterns: $L1_PATTERN_COUNT"
else
    echo "✗ No L1_N joints found in joint states"
fi

# Extract joint positions for L1_1 and L1_2 joints
echo "\nExtracting joint positions for L1_1 and L1_2 joints..."
JOINT_POSITIONS=$(grep -A 50 "position:" /tmp/joint_data.txt | grep -v "position:" | grep -v "velocity:" | grep -v "^$")
JOINT_NAMES=$(grep -A 50 "name:" /tmp/joint_data.txt | grep -v "name:" | grep -v "position:" | grep -v "^$")

# Convert to arrays
IFS=$'\n' JOINT_NAMES_ARRAY=($JOINT_NAMES)
IFS=$'\n' JOINT_POSITIONS_ARRAY=($JOINT_POSITIONS)

# Print positions for each joint type
echo "Joint positions by type:"
for ((i=0; i<${#JOINT_NAMES_ARRAY[@]}; i++)); do
    JOINT_NAME=${JOINT_NAMES_ARRAY[$i]}
    JOINT_POS=${JOINT_POSITIONS_ARRAY[$i]}
    
    if [[ $JOINT_NAME == *"L1_1"* ]]; then
        echo "  L1_1 Joint '$JOINT_NAME': Position = $JOINT_POS"
    elif [[ $JOINT_NAME == *"L1_2"* ]]; then
        echo "  L1_2 Joint '$JOINT_NAME': Position = $JOINT_POS"
    fi
done

# Detect gripper configuration
echo "\nDetecting gripper configuration..."

# First check TF data for multi-gripper pattern
MULTI_GRIPPER_PATTERN="_[0-9]_ezgripper"
TF_MULTI_PATTERN="gripper_[0-9]_ezgripper"

# Create TF data files if they don't exist (prevents grep errors)
if [ ! -f "/tmp/tf_static_data.txt" ]; then
    timeout 3 ros2 topic echo --once /tf_static | grep -A 50 -B 2 "ezgripper" > /tmp/tf_static_data.txt 2>/dev/null
fi

# Extract all frames from TF tree
echo "Extracting frames from TF tree..."
timeout 5 ros2 run tf2_ros tf2_echo dummy dummy 2>&1 | grep "Frames:" -A 1000 | grep -v "Frames:" > /tmp/tf_frames.txt 2>/dev/null

# Find all ezgripper frames in TF tree
echo "Frames with 'ezgripper' in TF tree:"
grep "ezgripper" /tmp/tf_frames.txt | sort

# Extract palm links from TF tree
echo "\nPalm links in TF tree:"
grep "ezgripper_palm_link" /tmp/tf_frames.txt | sort

# Extract knuckle joints from TF tree
echo "\nKnuckle joints in TF tree:"
grep "ezgripper_knuckle_palm" /tmp/tf_frames.txt | sort

# Check both joint data and TF data for gripper configuration
if grep -q "$MULTI_GRIPPER_PATTERN" /tmp/joint_data.txt 2>/dev/null; then
    echo "Detected multi-gripper configuration in joint data (double/triple)"
    # Extract gripper numbers from joint data
    GRIPPER_NUMBERS=$(grep -o "${PREFIX}_[0-9]_ezgripper" /tmp/joint_data.txt 2>/dev/null | sort | uniq | sed "s/${PREFIX}_\([0-9]\)_ezgripper/\1/g")
    echo "Found grippers in joint data: $GRIPPER_NUMBERS"
    GRIPPER_COUNT=$(echo "$GRIPPER_NUMBERS" | wc -l)
    echo "Total grippers from joint data: $GRIPPER_COUNT"
    GRIPPER_TYPE="multi"
elif grep -q "$TF_MULTI_PATTERN" /tmp/tf_static_data.txt 2>/dev/null; then
    echo "Detected multi-gripper configuration in TF data (double/triple)"
    # Extract gripper numbers from TF data
    GRIPPER_NUMBERS=$(grep -o "gripper_[0-9]" /tmp/tf_static_data.txt 2>/dev/null | sort | uniq | sed "s/gripper_\([0-9]\)/\1/g")
    echo "Found grippers in TF data: $GRIPPER_NUMBERS"
    GRIPPER_COUNT=$(echo "$GRIPPER_NUMBERS" | wc -w)
    echo "Total grippers from TF data: $GRIPPER_COUNT"
    GRIPPER_TYPE="multi"
    
    # Detect actual prefix from joint data
    ACTUAL_PREFIX=$(grep -o "[a-zA-Z0-9_]*_ezgripper_knuckle_palm" /tmp/joint_data.txt 2>/dev/null | sed "s/_ezgripper_knuckle_palm//g" | head -1)
    if [ -n "$ACTUAL_PREFIX" ]; then
        echo "Detected actual prefix from joint data: $ACTUAL_PREFIX"
        echo "NOTE: Using detected prefix '$ACTUAL_PREFIX' instead of specified prefix '$PREFIX'"
        PREFIX=$ACTUAL_PREFIX
    fi
else
    echo "Detected single gripper configuration"
    # Detect actual prefix from joint data for single gripper
    ACTUAL_PREFIX=$(grep -o "[a-zA-Z0-9_]*_ezgripper_knuckle_palm" /tmp/joint_data.txt 2>/dev/null | sed "s/_ezgripper_knuckle_palm//g" | head -1)
    if [ -n "$ACTUAL_PREFIX" ]; then
        echo "Detected actual prefix from joint data: $ACTUAL_PREFIX"
        if [ "$ACTUAL_PREFIX" != "$PREFIX" ]; then
            echo "WARNING: Detected prefix '$ACTUAL_PREFIX' does not match specified prefix '$PREFIX'"
            echo "NOTE: Using detected prefix '$ACTUAL_PREFIX' instead of specified prefix '$PREFIX'"
            PREFIX=$ACTUAL_PREFIX
        fi
    fi
    GRIPPER_TYPE="single"
fi

# Check for mismatch between TF tree and joint states
TF_PALM_COUNT=$(grep "ezgripper_palm_link" /tmp/tf_frames.txt | wc -l)
TF_KNUCKLE_COUNT=$(grep "ezgripper_knuckle_palm" /tmp/tf_frames.txt | wc -l)
JOINT_COUNT=$(grep -A 50 "name:" /tmp/joint_data.txt | grep -v "name:" | grep -v "position:" | grep -v "^$" | wc -l)

echo "\nTF tree analysis:"
echo "  Palm links in TF tree: $TF_PALM_COUNT"
echo "  Knuckle joints in TF tree: $TF_KNUCKLE_COUNT"
echo "  Joints in joint_states: $JOINT_COUNT"

# Compare TF prefixes with joint state prefixes
TF_PREFIXES=$(grep "ezgripper_palm_link" /tmp/tf_frames.txt | sed -E 's/(.+)_ezgripper_palm_link/\1/g' | sort | uniq)
echo "\nTF tree prefixes: $TF_PREFIXES"
echo "Joint state prefixes: $JOINT_PREFIXES"

if [ "$TF_KNUCKLE_COUNT" -gt 0 ] && [ "$JOINT_COUNT" -gt 0 ] && [ "$TF_KNUCKLE_COUNT" -ne "$JOINT_COUNT" ]; then
    echo "\nWARNING: Mismatch between TF tree ($TF_KNUCKLE_COUNT knuckle joints) and joint states ($JOINT_COUNT joints)"
    echo "This could indicate a configuration issue between the URDF and joint publisher"
fi

# Check for prefix mismatches
if [ -n "$TF_PREFIXES" ] && [ -n "$JOINT_PREFIXES" ]; then
    echo "\nChecking for prefix mismatches:"
    for TF_PREFIX in $TF_PREFIXES; do
        if ! echo "$JOINT_PREFIXES" | grep -q "$TF_PREFIX"; then
            echo "WARNING: TF prefix '$TF_PREFIX' not found in joint states"
        fi
    done

    for JOINT_PREFIX in $JOINT_PREFIXES; do
        if ! echo "$TF_PREFIXES" | grep -q "$JOINT_PREFIX"; then
            echo "WARNING: Joint prefix '$JOINT_PREFIX' not found in TF tree"
        fi
    done
fi

# Double-check for actual prefix in joint data if we haven't already detected it
if [ "$GRIPPER_TYPE" = "single" ] && [ "$PREFIX" != "$ACTUAL_PREFIX" ]; then
    ACTUAL_PREFIX=$(grep -o "[a-zA-Z0-9_]*_ezgripper_knuckle_palm" /tmp/joint_data.txt 2>/dev/null | sed "s/_ezgripper_knuckle_palm//g" | head -1)
    if [ -n "$ACTUAL_PREFIX" ]; then
        echo "Detected actual prefix from joint data: $ACTUAL_PREFIX"
        echo "NOTE: Using detected prefix '$ACTUAL_PREFIX' instead of specified prefix '$PREFIX'"
        PREFIX=$ACTUAL_PREFIX
    fi
fi
echo ""

echo "=== TF Static Topic Info (Filtered for EZGripper) ==="
echo "--- /tf_static (filtered for ezgripper) ---"
timeout 3 ros2 topic echo --once /tf_static 2>/dev/null | grep -A 3 -B 3 "ezgripper" || echo "No EZGripper transforms found"
echo ""

echo "=== TF Topic Info (Filtered for EZGripper) ==="
echo "--- /tf (filtered for ezgripper) ---"
timeout 3 ros2 topic echo --once /tf 2>/dev/null | grep -A 3 -B 3 "ezgripper" || echo "No EZGripper transforms found"
echo ""

echo "=== Generating TF Tree Visualization ==="
timeout 10 ros2 run tf2_tools view_frames
echo "TF tree visualization saved to frames.pdf (if successful)"

# Open the PDF if it exists
if [ -f "frames.pdf" ]; then
    echo "Opening frames.pdf..."
    xdg-open frames.pdf &
fi

echo "=== Checking TF Tree for Errors ==="

# Get all frames from the TF tree
echo "Analyzing TF tree structure..."
TF_FRAMES=$(timeout 3 ros2 run tf2_tools view_frames 2>&1 | grep -A 1000 "Result:" | grep -v "Result:")
echo "$TF_FRAMES" > /tmp/tf_frames.txt

# Check if we have any frames at all
if [ -z "$TF_FRAMES" ]; then
    echo "ERROR: No frames found in the TF tree!"
else
    echo "Found frames in the TF tree."
    
    # Check for gripper configurations in TF tree
    echo "\nChecking for gripper configurations in TF tree:"
    
    # First check for standard single gripper (without gripper_N_ prefix)
    STANDARD_PREFIXES=$(grep "ezgripper_palm_link" /tmp/tf_frames.txt | grep -v "gripper_[0-9]\+_ezgripper" | sed -E 's/(.+)_ezgripper_palm_link/\1/g' | sort -u)
    
    # Then find all numbered gripper prefixes in the TF tree
    NUMBERED_PREFIXES=$(grep -o "gripper_[0-9]\+_ezgripper" /tmp/tf_frames.txt | sed 's/_ezgripper//' | sort -u)
    
    # Combine both types of prefixes
    ALL_PREFIXES="$STANDARD_PREFIXES $NUMBERED_PREFIXES"
    
    if [ -z "$ALL_PREFIXES" ]; then
        echo "✗ No gripper prefixes found in TF tree"
    else
        echo "Found the following gripper prefixes in TF tree:"
        
        # Process standard prefixes first
        for PREFIX in $STANDARD_PREFIXES; do
            GRIPPER_FRAMES=$(grep "${PREFIX}_ezgripper" /tmp/tf_frames.txt || echo "")
            FRAME_COUNT=$(echo "$GRIPPER_FRAMES" | grep -v "^$" | wc -l)
            echo "✓ $PREFIX (standard): $FRAME_COUNT frames"
        done
        
        # Then process numbered prefixes
        for PREFIX in $NUMBERED_PREFIXES; do
            GRIPPER_FRAMES=$(grep "${PREFIX}_ezgripper" /tmp/tf_frames.txt || echo "")
            FRAME_COUNT=$(echo "$GRIPPER_FRAMES" | grep -v "^$" | wc -l)
            echo "✓ $PREFIX (numbered): $FRAME_COUNT frames"
        done
        
        # Count total number of grippers
        GRIPPER_COUNT=$(echo "$ALL_PREFIXES" | wc -w)
        echo "\nTotal number of grippers detected in TF tree: $GRIPPER_COUNT"
    fi
    
    # Save all prefixes for later use
    GRIPPER_PREFIXES="$ALL_PREFIXES"
    
    # Check for frames with the prefix to ensure our gripper is in the tree
    GRIPPER_FRAMES=$(echo "$TF_FRAMES" | grep "${PREFIX}_ezgripper")
    
    if [ -n "$GRIPPER_FRAMES" ]; then
        echo "\nFound gripper frames with prefix '${PREFIX}':"
        echo "$GRIPPER_FRAMES" | head -n 5
        if [ $(echo "$GRIPPER_FRAMES" | wc -l) -gt 5 ]; then
            echo "... and $(($(echo "$GRIPPER_FRAMES" | wc -l) - 5)) more frames"
        fi
    else
        echo "\nWARNING: No gripper frames found with prefix '${PREFIX}'!"
    fi
    
    echo "\nChecking critical EZGripper connections:"
    
    # Check if palm is connected to base_link
    timeout 3 ros2 run tf2_ros tf2_echo "base_link" "${PREFIX}_ezgripper_palm_link" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ base_link -> ${PREFIX}_ezgripper_palm_link: Connected"
    else
        echo "✗ base_link -> ${PREFIX}_ezgripper_palm_link: NOT CONNECTED"
    fi
    
    # Check if fingers are connected to palm
    timeout 3 ros2 run tf2_ros tf2_echo "${PREFIX}_ezgripper_palm_link" "${PREFIX}_ezgripper_finger_L1_1" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ ${PREFIX}_ezgripper_palm_link -> ${PREFIX}_ezgripper_finger_L1_1: Connected"
    else
        echo "✗ ${PREFIX}_ezgripper_palm_link -> ${PREFIX}_ezgripper_finger_L1_1: NOT CONNECTED"
    fi
    
    # Check if finger links are connected (L1 to L2)
    timeout 3 ros2 run tf2_ros tf2_echo "${PREFIX}_ezgripper_finger_L1_1" "${PREFIX}_ezgripper_finger_L2_1" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ ${PREFIX}_ezgripper_finger_L1_1 -> ${PREFIX}_ezgripper_finger_L2_1: Connected"
    else
        echo "✗ ${PREFIX}_ezgripper_finger_L1_1 -> ${PREFIX}_ezgripper_finger_L2_1: NOT CONNECTED"
    fi
    
    # Check second finger connections
    timeout 3 ros2 run tf2_ros tf2_echo "${PREFIX}_ezgripper_palm_link" "${PREFIX}_ezgripper_finger_L1_2" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ ${PREFIX}_ezgripper_palm_link -> ${PREFIX}_ezgripper_finger_L1_2: Connected"
    else
        echo "✗ ${PREFIX}_ezgripper_palm_link -> ${PREFIX}_ezgripper_finger_L1_2: NOT CONNECTED"
    fi
    
    # Check finger pad connections
    timeout 3 ros2 run tf2_ros tf2_echo "${PREFIX}_ezgripper_finger_L2_1" "${PREFIX}_ezgripper_finger_pad_1" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ ${PREFIX}_ezgripper_finger_L2_1 -> ${PREFIX}_ezgripper_finger_pad_1: Connected"
    else
        echo "✗ ${PREFIX}_ezgripper_finger_L2_1 -> ${PREFIX}_ezgripper_finger_pad_1: NOT CONNECTED"
    fi
fi

echo "\n=== Checking Joint Names in Joint State Messages ==="
JOINT_NAMES=$(timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null | grep -A 50 "name:" | grep -v "name:" | grep -v "position:" | sed 's/^- //')

# Check for gripper configurations in joint states
echo "Checking for gripper configurations in joint states:"

# First check for standard single gripper (without gripper_N_ prefix)
STANDARD_PREFIXES_JOINTS=$(grep "ezgripper_knuckle_palm" /tmp/joint_data.txt | grep -v "gripper_[0-9]\+_ezgripper" | sed -E 's/- (.+)_ezgripper_knuckle_palm.+/\1/g' | sort -u)

# Then find all numbered gripper prefixes in the joint states
NUMBERED_PREFIXES_JOINTS=$(grep -o "gripper_[0-9]\+_ezgripper" /tmp/joint_data.txt | sed 's/_ezgripper//' | sort -u)

# Combine both types of prefixes
GRIPPER_PREFIXES_JOINTS="$STANDARD_PREFIXES_JOINTS $NUMBERED_PREFIXES_JOINTS"

if [ -z "$GRIPPER_PREFIXES_JOINTS" ]; then
    echo "✗ No gripper prefixes found in joint states"
else
    echo "Found the following gripper prefixes in joint states:"
    for PREFIX in $GRIPPER_PREFIXES_JOINTS; do
        GRIPPER_JOINTS=$(grep "${PREFIX}_ezgripper" /tmp/joint_data.txt || echo "")
        JOINT_COUNT=$(echo "$GRIPPER_JOINTS" | grep -v "^$" | wc -l)
        echo "✓ $PREFIX: $JOINT_COUNT joints"
        echo "  Joints: $(echo "$GRIPPER_JOINTS" | head -n 3 | sed 's/^- //')"
        if [ $JOINT_COUNT -gt 3 ]; then
            echo "  ... and $(($JOINT_COUNT - 3)) more joints"
        fi
        
        # Check for L1_N joints for this prefix
        L1_JOINTS=$(echo "$GRIPPER_JOINTS" | grep "L1_" | sed 's/^- //')
        echo "  L1 joints: $(echo "$L1_JOINTS" | tr '\n' ' ')"
    done
    
    # Count total number of grippers in joint states
    GRIPPER_COUNT_JOINTS=$(echo "$GRIPPER_PREFIXES_JOINTS" | wc -l)
    echo "\nTotal number of grippers detected in joint states: $GRIPPER_COUNT_JOINTS"
    
    # Check for mismatches between TF tree and joint states
    if [ -n "$GRIPPER_PREFIXES" ] && [ -n "$GRIPPER_PREFIXES_JOINTS" ]; then
        echo "\nChecking for mismatches between TF tree and joint states:"
        for PREFIX in $GRIPPER_PREFIXES; do
            if ! echo "$GRIPPER_PREFIXES_JOINTS" | grep -q "$PREFIX"; then
                echo "✗ WARNING: Gripper prefix '$PREFIX' found in TF tree but not in joint states"
            fi
        done
        
        for PREFIX in $GRIPPER_PREFIXES_JOINTS; do
            if ! echo "$GRIPPER_PREFIXES" | grep -q "$PREFIX"; then
                echo "✗ WARNING: Gripper prefix '$PREFIX' found in joint states but not in TF tree"
            fi
        done
    fi
fi

if [ -n "$JOINT_NAMES" ]; then
    echo "Joint names in /ezgripper/joint_states:"
    echo "$JOINT_NAMES"
    
    # Check if joint names match the expected pattern with the correct prefix
    if [ "$GRIPPER_TYPE" = "multi" ]; then
        # For multi-gripper, dynamically detect and check each gripper
        for i in $GRIPPER_NUMBERS; do
            MATCHING_JOINTS=$(echo "$JOINT_NAMES" | grep "${PREFIX}_${i}_ezgripper")
            if [ -n "$MATCHING_JOINTS" ]; then
                echo "✓ Found joints for gripper ${i} with prefix '${PREFIX}_${i}'."
                
                # Check for L1_1 and L1_2 joints
                L1_1_JOINT=$(echo "$MATCHING_JOINTS" | grep "L1_1")
                L1_2_JOINT=$(echo "$MATCHING_JOINTS" | grep "L1_2")
                
                if [ -n "$L1_1_JOINT" ] && [ -n "$L1_2_JOINT" ]; then
                    echo "  ✓ Found both L1_1 and L1_2 joints for gripper ${i}."
                    
                    # Get joint positions to check inversion
                    JOINT_DATA=$(timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null)
                    
                    # Extract position for L1_1 joint
                    L1_1_POS=$(echo "$JOINT_DATA" | grep -A 50 "name:" | grep -n "${PREFIX}_${i}_ezgripper_knuckle_palm_L1_1" | cut -d ':' -f 1)
                    if [ -n "$L1_1_POS" ]; then
                        L1_1_POS=$((L1_1_POS + 50))
                        L1_1_VAL=$(echo "$JOINT_DATA" | grep -A 50 "position:" | sed -n "${L1_1_POS}p" | tr -d '- ')
                        echo "  L1_1 Position: $L1_1_VAL"
                    fi
                    
                    # Extract position for L1_2 joint
                    L1_2_POS=$(echo "$JOINT_DATA" | grep -A 50 "name:" | grep -n "${PREFIX}_${i}_ezgripper_knuckle_palm_L1_2" | cut -d ':' -f 1)
                    if [ -n "$L1_2_POS" ]; then
                        L1_2_POS=$((L1_2_POS + 50))
                        L1_2_VAL=$(echo "$JOINT_DATA" | grep -A 50 "position:" | sed -n "${L1_2_POS}p" | tr -d '- ')
                        echo "  L1_2 Position: $L1_2_VAL"
                    fi
                else
                    echo "  ✗ Missing L1_1 or L1_2 joint for gripper ${i}."
                fi
            else
                echo "✗ No joints found for gripper ${i} with prefix '${PREFIX}_${i}'!"
            fi
        done
    else
        # For single gripper
        MATCHING_JOINTS=$(echo "$JOINT_NAMES" | grep "${PREFIX}_ezgripper")
        if [ -n "$MATCHING_JOINTS" ]; then
            echo "✓ Found joints with correct prefix '${PREFIX}'."
            
            # Check for L1_1 and L1_2 joints
            L1_1_JOINT=$(echo "$MATCHING_JOINTS" | grep "L1_1")
            L1_2_JOINT=$(echo "$MATCHING_JOINTS" | grep "L1_2")
            
            if [ -n "$L1_1_JOINT" ] && [ -n "$L1_2_JOINT" ]; then
                echo "  ✓ Found both L1_1 and L1_2 joints."
                
                # Get joint positions to check inversion
                JOINT_DATA=$(timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null)
                
                # Extract position for L1_1 joint
                L1_1_POS=$(echo "$JOINT_DATA" | grep -A 50 "name:" | grep -n "${PREFIX}_ezgripper_knuckle_palm_L1_1" | cut -d ':' -f 1)
                if [ -n "$L1_1_POS" ]; then
                    L1_1_POS=$((L1_1_POS + 50))
                    L1_1_VAL=$(echo "$JOINT_DATA" | grep -A 50 "position:" | sed -n "${L1_1_POS}p" | tr -d '- ')
                    echo "  L1_1 Position: $L1_1_VAL"
                fi
                
                # Extract position for L1_2 joint
                L1_2_POS=$(echo "$JOINT_DATA" | grep -A 50 "name:" | grep -n "${PREFIX}_ezgripper_knuckle_palm_L1_2" | cut -d ':' -f 1)
                if [ -n "$L1_2_POS" ]; then
                    L1_2_POS=$((L1_2_POS + 50))
                    L1_2_VAL=$(echo "$JOINT_DATA" | grep -A 50 "position:" | sed -n "${L1_2_POS}p" | tr -d '- ')
                    echo "  L1_2 Position: $L1_2_VAL"
                fi
            else
                echo "  ✗ Missing L1_1 or L1_2 joint."
            fi
        else
            echo "✗ ERROR: No joints found with correct prefix '${PREFIX}'!"
            echo "This indicates a mismatch between TF frames and joint names."
        fi
    fi
else
    echo "No joint names found in /ezgripper/joint_states."
fi

# Generate URDF for analysis
echo "\n=== Generating Expanded URDF for Analysis ==="
# Dynamically determine URDF path based on detected configuration
if [ "$GRIPPER_TYPE" = "multi" ]; then
    # Try to find the appropriate XACRO file based on the number of grippers
    if [ "$GRIPPER_COUNT" -eq 3 ]; then
        echo "Using triple gripper XACRO file"
        URDF_PATH="/home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/urdf/ezgripper_triple_with_mount.urdf.xacro"
    elif [ "$GRIPPER_COUNT" -eq 2 ]; then
        echo "Using double gripper XACRO file"
        URDF_PATH="/home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/urdf/ezgripper_double_with_mount.urdf.xacro"
        # If file doesn't exist, fall back to triple
        if [ ! -f "$URDF_PATH" ]; then
            echo "Double gripper XACRO not found, falling back to triple gripper XACRO"
            URDF_PATH="/home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/urdf/ezgripper_triple_with_mount.urdf.xacro"
        fi
    else
        echo "Using triple gripper XACRO file (fallback for multi-gripper)"
        URDF_PATH="/home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/urdf/ezgripper_triple_with_mount.urdf.xacro"
    fi
else
    echo "Using single gripper XACRO file"
    URDF_PATH="/home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/urdf/ezgripper_single_mount.urdf.xacro"
fi

# Check if the file exists
if [ ! -f "$URDF_PATH" ]; then
    echo "ERROR: XACRO file not found at $URDF_PATH"
    # List available XACRO files
    echo "Available XACRO files:"
    find /home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/urdf -name "*.xacro" | sort
fi

echo "Expanding XACRO file: $URDF_PATH"
# For multi-gripper configurations, we need to use a different parameter format
if [ "$GRIPPER_TYPE" = "multi" ]; then
    # For triple/double gripper, use the parent prefix
    ros2 run xacro xacro $URDF_PATH parent_prefix:=$PREFIX > /tmp/expanded_gripper.urdf
else
    # For single gripper
    ros2 run xacro xacro $URDF_PATH prefix:=$PREFIX > /tmp/expanded_gripper.urdf
fi

echo "Analyzing joint definitions in URDF..."
echo "L1_1 Joints:"
grep -A 10 "joint.*knuckle_palm_L1_1" /tmp/expanded_gripper.urdf | head -15
echo "\nL1_2 Joints:"
grep -A 10 "joint.*knuckle_palm_L1_2" /tmp/expanded_gripper.urdf | head -15

# Test joint movement
echo "\n=== Testing Joint Movement ==="

# Get all detected gripper prefixes from TF tree
DETECTED_PREFIXES=""

# First check for standard prefixes (without gripper_N_)
if [ -n "$STANDARD_PREFIXES" ]; then
    DETECTED_PREFIXES="$STANDARD_PREFIXES"
    echo "Found standard gripper prefixes: $STANDARD_PREFIXES"
fi

# Then check for numbered prefixes (gripper_N)
if [ -n "$NUMBERED_PREFIXES" ]; then
    DETECTED_PREFIXES="$DETECTED_PREFIXES $NUMBERED_PREFIXES"
    echo "Found numbered gripper prefixes: $NUMBERED_PREFIXES"
fi

# If no prefixes detected, use the default prefix and also add "gripper"
if [ -z "$DETECTED_PREFIXES" ]; then
    echo "No gripper prefixes detected, using default prefix: $PREFIX"
    DETECTED_PREFIXES="$PREFIX gripper"
else
    # Always add the generic "gripper" prefix for multi-gripper setups
    if [ -n "$NUMBERED_PREFIXES" ] && ! echo "$DETECTED_PREFIXES" | grep -q "\bgripper\b"; then
        DETECTED_PREFIXES="$DETECTED_PREFIXES gripper"
        echo "Added generic 'gripper' prefix for multi-gripper control"
    fi
fi

# Check for active command topics
echo "\nChecking for active command topics:"
COMMAND_TOPICS=$(timeout 3 ros2 topic list | grep "/ezgripper/.*command" || echo "")

if [ -n "$COMMAND_TOPICS" ]; then
    echo "Found command topics:"
    echo "$COMMAND_TOPICS"
    
    # Check if each topic has subscribers
    echo "\nChecking for subscribers on command topics:"
    for TOPIC in $COMMAND_TOPICS; do
        SUB_COUNT=$(timeout 2 ros2 topic info "$TOPIC" 2>/dev/null | grep "Subscription count: " | sed 's/.*count: \([0-9]\+\).*/\1/' || echo "0")
        echo "$TOPIC: $SUB_COUNT subscriber(s)"
    done
else
    echo "No command topics found. Joint publisher may not be running."
fi

# Test each detected gripper
for GRIPPER_PREFIX in $DETECTED_PREFIXES; do
    # Remove any leading/trailing whitespace
    GRIPPER_PREFIX=$(echo "$GRIPPER_PREFIX" | xargs)
    
    # Clean the prefix - replace spaces with underscores
    CLEAN_PREFIX=$(echo "$GRIPPER_PREFIX" | tr ' ' '_')
    
    # Create clean topic name (no spaces)
    TOPIC_NAME="/ezgripper/${CLEAN_PREFIX}/command"
    
    echo "\nTesting gripper with prefix: $GRIPPER_PREFIX"
    echo "Sending command to open gripper (value 100) on topic: $TOPIC_NAME"
    
    # Check if there are subscribers for this topic
    SUB_COUNT=$(timeout 2 ros2 topic info "$TOPIC_NAME" 2>/dev/null | grep "Subscription count: [1-9]" | wc -l || echo "0")
    
    if [ "$SUB_COUNT" -gt 0 ]; then
        echo "Topic has subscribers. Sending command..."
        # Try both Float32 and Float64 message types (for compatibility)
        ros2 topic pub --once "$TOPIC_NAME" std_msgs/msg/Float32 "{data: 100.0}" 2>/dev/null || \
        ros2 topic pub --once "$TOPIC_NAME" std_msgs/msg/Float64 "{data: 100.0}" 2>/dev/null
        sleep 1
        
        # Get joint positions after command
        echo "Joint positions after open command:"
        timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null | grep -A 20 "position:" | head -10 || echo "No joint positions received"
        
        echo "Sending command to close gripper (value 0)"
        ros2 topic pub --once "$TOPIC_NAME" std_msgs/msg/Float32 "{data: 0.0}" 2>/dev/null || \
        ros2 topic pub --once "$TOPIC_NAME" std_msgs/msg/Float64 "{data: 0.0}" 2>/dev/null
        sleep 1
        
        # Get joint positions after command
        echo "Joint positions after close command:"
        timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null | grep -A 20 "position:" | head -10 || echo "No joint positions received"
    else
        echo "No subscribers found for topic $TOPIC_NAME. Skipping command test."
    fi
done

# Also test the default gripper command topic
DEFAULT_TOPIC="/ezgripper/gripper/command"
echo "\nTesting default gripper command topic: $DEFAULT_TOPIC"

# Check if there are subscribers for the default topic
DEFAULT_SUB_COUNT=$(timeout 2 ros2 topic info "$DEFAULT_TOPIC" 2>/dev/null | grep "Subscription count: [1-9]" | wc -l || echo "0")

if [ "$DEFAULT_SUB_COUNT" -gt 0 ]; then
    echo "Default topic has subscribers. Sending command..."
    echo "Sending command to open default gripper (value 100)"
    ros2 topic pub --once "$DEFAULT_TOPIC" std_msgs/msg/Float32 "{data: 100.0}" 2>/dev/null || \
    ros2 topic pub --once "$DEFAULT_TOPIC" std_msgs/msg/Float64 "{data: 100.0}" 2>/dev/null
    sleep 1

    echo "Joint positions after default open command:"
    timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null | grep -A 20 "position:" | head -10 || echo "No joint positions received"
    
    echo "Sending command to close default gripper (value 0)"
    ros2 topic pub --once "$DEFAULT_TOPIC" std_msgs/msg/Float32 "{data: 0.0}" 2>/dev/null || \
    ros2 topic pub --once "$DEFAULT_TOPIC" std_msgs/msg/Float64 "{data: 0.0}" 2>/dev/null
    sleep 1
    
    echo "Joint positions after default close command:"
    timeout 3 ros2 topic echo --once /ezgripper/joint_states 2>/dev/null | grep -A 20 "position:" | head -10 || echo "No joint positions received"
else
    echo "No subscribers found for default topic $DEFAULT_TOPIC. Skipping command test."
fi

echo "\n=== Debug Complete ==="
echo "Check the TF tree visualization in frames.pdf"
echo "Expanded URDF available at /tmp/expanded_gripper.urdf"
echo "Joint data available at /tmp/joint_data.txt"
