# Triple Gripper Orientation Testing Guide

This document outlines a methodical approach to testing different transform configurations for the EZGripper triple gripper to ensure correct finger orientation.

## Background

The triple gripper consists of three single grippers mounted on a common base. Each gripper has its own coordinate frame and orientation. The orientation is defined by roll, pitch, and yaw angles (in radians) in the static transform publisher.

## Key Transform Points

There are two critical transform points that affect the finger orientation:

1. **Palm to Knuckle Transform**: Defines how the knuckle is oriented relative to the palm
2. **Knuckle to Finger Transform**: Defines how the finger is oriented relative to the knuckle

## Testing Matrix

We'll systematically test different combinations of orientations at these transform points to find the correct configuration.

### Palm to Knuckle Transform Variations

For each gripper (1, 2, 3), we'll test the following variations:

| Test ID | Description | Roll | Pitch | Yaw |
|---------|-------------|------|-------|-----|
| PK-1 | Original | Gripper 1: 1.5708<br>Gripper 2: -1.5708<br>Gripper 3: 0.0 | Gripper 1: 0.0<br>Gripper 2: 0.0<br>Gripper 3: 1.5708 | 0.0 |
| PK-2 | Rotate 180° around Z | Gripper 1: 1.5708<br>Gripper 2: -1.5708<br>Gripper 3: 0.0 | Gripper 1: 0.0<br>Gripper 2: 0.0<br>Gripper 3: 1.5708 | 3.14159 |
| PK-3 | Rotate 180° around X | Gripper 1: 1.5708 + 3.14159<br>Gripper 2: -1.5708 + 3.14159<br>Gripper 3: 3.14159 | Gripper 1: 0.0<br>Gripper 2: 0.0<br>Gripper 3: 1.5708 | 0.0 |
| PK-4 | Rotate 180° around Y | Gripper 1: 1.5708<br>Gripper 2: -1.5708<br>Gripper 3: 0.0 | Gripper 1: 3.14159<br>Gripper 2: 3.14159<br>Gripper 3: 1.5708 + 3.14159 | 0.0 |

### Knuckle to Finger Transform Variations

For each gripper (1, 2, 3), we'll test the following variations:

| Test ID | Description | Roll | Pitch | Yaw |
|---------|-------------|------|-------|-----|
| KF-1 | Original | 0.0 | 0.0 | 0.0 |
| KF-2 | Rotate 180° around Z | 0.0 | 0.0 | 3.14159 |
| KF-3 | Rotate 180° around X | 3.14159 | 0.0 | 0.0 |
| KF-4 | Rotate 180° around Y | 0.0 | 3.14159 | 0.0 |

## Testing Procedure

1. For each test configuration:
   - Update the `gripper_static_tf_publisher.py` file with the specified transforms
   - Build the package: `colcon build --packages-select ezgripper_description`
   - Source the workspace: `source install/setup.bash`
   - Launch the triple gripper: `ros2 launch ezgripper_description ezgripper_triple_standalone.launch.py`
   - Observe the finger orientation in RViz
   - Record the results

## Progress Tracking

### Current Configuration: PK-1 + KF-1 (Original baseline)

**Status:** Tested - Issues Found

**Description:** 
- Palm to Knuckle: Original orientation
- Knuckle to Finger: Original orientation (0,0,0)

**Results:**
- The palm is on the wrong side of the mounting plate
- The fingers are reversed on the palm

**Code:**
```python
# Palm to Knuckle transforms (original)
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=0.0595, y=0.03, z=0.0,
    roll=1.5708, pitch=0.0, yaw=0.0
)

# Knuckle to Finger transforms (original)
self.publish_static_transform(
    parent_frame=f'{prefix}_knuckle_palm_L1_1',
    child_frame=f'{prefix}_finger_L1_1',
    x=0.0, y=0.0, z=0.0,
    roll=0.0, pitch=0.0, yaw=0.0
)
```

### Current Configuration: PK-2 + KF-1 (180° Z rotation for palm, original finger)

**Status:** Tested - Partial Improvement

**Description:** 
- Palm to Knuckle: 180° rotation around Z axis
- Knuckle to Finger: Original orientation (0,0,0)

**Results:**
- Fingers are now correctly oriented
- Palm is still on the wrong side of the mounting plate

**Code:**
```python
# Palm to Knuckle transforms (180° Z rotation)
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=0.0595, y=0.03, z=0.0,
    roll=1.5708, pitch=0.0, yaw=3.14159  # Added 180° rotation around Z
)

# Knuckle to Finger transforms (original)
self.publish_static_transform(
    parent_frame=f'{prefix}_knuckle_palm_L1_1',
    child_frame=f'{prefix}_finger_L1_1',
    x=0.0, y=0.0, z=0.0,
    roll=0.0, pitch=0.0, yaw=0.0
)
```

### Current Configuration: PK-4 + KF-1 (180° Y rotation for palm, original finger)

**Status:** Tested - Partial Improvement

**Description:** 
- Palm to Knuckle: 180° rotation around Y axis to reverse palm direction
- Knuckle to Finger: Original orientation (0,0,0)

**Results:**
- Relationship between fingers and palm is now correct
- Relationship between palm and mount still needs to be reversed by 180 degrees

**Code:**
```python
# Palm to Knuckle transforms (180° Y rotation)
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=0.0595, y=0.03, z=0.0,
    roll=1.5708, pitch=3.14159, yaw=3.14159  # Added 180° rotation around Y and Z
)

# Knuckle to Finger transforms (original)
self.publish_static_transform(
    parent_frame=f'{prefix}_knuckle_palm_L1_1',
    child_frame=f'{prefix}_finger_L1_1',
    x=0.0, y=0.0, z=0.0,
    roll=0.0, pitch=0.0, yaw=0.0
)
```

### Current Configuration: Mount-Palm 180° Rotation

**Status:** Tested - Issues Found

**Description:** 
- Mount to Palm: 180° rotation to reverse the relationship
- Palm to Knuckle: Same as previous test (PK-4)
- Knuckle to Finger: Original orientation (KF-1)

**Results:**
- The transforms moved the grippers from being stacked to being laid in parallel
- This is not the desired configuration

### Current Configuration: Negative X Offset

**Status:** Tested - Issues Found

**Description:** 
- Palm to Knuckle: 180° Z rotation with negative X offset to reverse palm direction
- Knuckle to Finger: Original orientation (KF-1)

**Results:**
- The palm orientation was still not correct

**Code:**
```python
# First finger - with 180° Z rotation and modified X offset
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=-0.0595, y=0.03, z=0.0,  # Negative X to reverse palm direction
    roll=1.5708, pitch=0.0, yaw=3.14159  # 90 degrees around X, 180 degrees around Z
)
```

### Current Configuration: Flipped Palm Orientation

**Status:** Tested - Issues Found

**Description:** 
- Palm to Knuckle: Flipped Y coordinates and adjusted pitch to flip palm 180 degrees around Z axis
- Knuckle to Finger: Original orientation (KF-1)

**Results:**
- The approach of modifying the static transforms was not effective

**Code:**
```python
# First finger - with flipped palm orientation
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=0.0595, y=-0.03, z=0.0,  # Flipped Y coordinate
    roll=1.5708, pitch=0.0, yaw=0.0  # 90 degrees around X
)
```

### Current Configuration: XACRO-Level Rotation

**Status:** Tested - Issues Found

**Description:** 
- Modified the XACRO file to rotate the entire gripper assembly 180 degrees around the Z axis
- Reverted the palm-to-knuckle transforms to their original values

**Results:**
- This approach was not correct for the specific issue we're trying to solve

**Code:**
```xml
<!-- Rotate the entire gripper assembly 180 degrees around the Z axis (pi radians) -->
<xacro:ezgripper_triple_with_mount 
    prefix="$(arg prefix)" 
    parent_link="base_link">
    <origin xyz="${ezgripper_offset_x} ${ezgripper_offset_y} ${ezgripper_offset_z}" rpy="0 0 3.14159"/>
</xacro:ezgripper_triple_with_mount>
```

### Current Configuration: Flipped Palm in Static TF Publisher

**Status:** Tested - Issues Found

**Description:** 
- Modified the static transform publisher to flip the palm 180 degrees around the Z axis
- Used negative X and Y coordinates along with 180° Z rotation (3.14159 yaw)

**Results:**
- This approach was not correct as it was duplicating the rotation already present in the XACRO file

**Code:**
```python
# First finger - with 180° Z rotation
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=-0.0595, y=-0.03, z=0.0,  # Negative X and Y to flip 180° around Z
    roll=1.5708, pitch=0.0, yaw=3.14159  # 90 degrees around X, 180 degrees around Z
)
```

### Current Configuration: Original Static Transforms

**Status:** Tested - Issues Found

**Description:** 
- Reverted to the original static transforms to match the XACRO file
- The XACRO file had `rpy="0 0 ${pi}"` (180 degrees around Z) for each gripper

**Results:**
- The orientation was still incorrect, suggesting the issue might be with the XACRO file itself

**Code:**
```python
# First finger - matches URDF joint origin
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=0.0595, y=0.03, z=0.0,
    roll=1.5708, pitch=0.0, yaw=0.0  # 90 degrees in radians around X
)
```

### Current Configuration: Modified XACRO Orientation

**Status:** Tested - Issues Found

**Description:** 
- Changed the RPY values in the XACRO file from `rpy="0 0 ${pi}"` to `rpy="0 0 0"` for each gripper
- Kept the original static transforms in the gripper_static_tf_publisher.py file

**Results:**
- The relationship between the gripper and mount was correct, but the fingers needed to be flipped along the X axis

**Code:**
```xml
<!-- Changed from rpy="0 0 ${pi}" to rpy="0 0 0" -->
<xacro:ezgripper_single prefix="${prefix}_1" parent_link="${prefix}_ezgripper_to_mount">
  <origin xyz="${gripper_offset} 0 ${gripper_spacing}" rpy="0 0 0"/>
</xacro:ezgripper_single>
```

### Current Configuration: Flipped Fingers Along X Axis

**Status:** Tested - Issues Found

**Description:** 
- Reverted the XACRO file to its original state with `rpy="0 0 ${pi}"` for each gripper
- Modified the static transform publisher to flip the fingers along the X axis by adding a 180-degree rotation

**Results:**
- The issue was identified as being in the XACRO file, not in the static transform publisher

**Code:**
```python
# First finger - with 180° X rotation
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=0.0595, y=0.03, z=0.0,
    roll=1.5708 + 3.14159, pitch=0.0, yaw=0.0  # 90 degrees + 180 degrees around X
)
```

### Current Configuration: Corrected XACRO Orientation

**Status:** Tested - Partially Fixed

**Description:** 
- Changed the RPY values in the XACRO file from `rpy="0 0 ${pi}"` to `rpy="0 0 0"` for each gripper-to-mount connection
- Reverted the static transform publisher to its original configuration

**Results:**
- The mount-to-palm relationship is now correct
- The fingers in the triple gripper are still flipped
- The single gripper is working correctly

**Code:**
```xml
<!-- Changed from rpy="0 0 ${pi}" to rpy="0 0 0" -->
<xacro:ezgripper_single prefix="${prefix}_1" parent_link="${prefix}_ezgripper_to_mount">
  <origin xyz="${gripper_offset} 0 ${gripper_spacing}" rpy="0 0 0"/>
</xacro:ezgripper_single>
```

### Current Configuration: Conditional Finger Flipping

**Status:** Tested - Issues Found

**Description:** 
- Kept the XACRO file with `rpy="0 0 0"` for each gripper-to-mount connection
- Modified the static transform publisher to conditionally flip the fingers for the triple gripper
- Single gripper uses the original transforms

**Results:**
- This approach works but is not the proper way to handle joint orientations
- Static transform publisher should not be used for joints that are actually dynamic

**Code:**
```python
# Check if this is a triple gripper (has '_1', '_2', '_3' in the prefix)
is_triple_gripper = '_1_' in prefix or '_2_' in prefix or '_3_' in prefix

if is_triple_gripper:
    # For triple gripper, flip the fingers along the X axis
    # First finger (reflectY=1) - with 180° X rotation
    self.publish_static_transform(
        parent_frame=f'{prefix}_palm_link',
        child_frame=f'{prefix}_knuckle_palm_L1_1',
        x=0.0595, y=0.03, z=0.0,
        roll=1.5708 + 3.14159, pitch=0.0, yaw=0.0  # 90 degrees + 180 degrees around X
    )
```

### Current Configuration: Dedicated Triple Gripper XACRO

**Status:** Testing next

**Description:** 
- Created a dedicated XACRO file for the triple gripper with properly oriented joints
- Modified the triple gripper mount XACRO to use the new triple gripper definition
- Reverted the static transform publisher to its original configuration

**Code:**
```xml
<!-- Define a modified knuckle joint macro for the triple gripper -->
<xacro:macro name="ezgripper_triple_knuckle_palm_L1" params="prefix postfix reflectY reflectZ reflectR mimic_test">
    <joint name="${prefix}_ezgripper_knuckle_palm_L1_${postfix}" type="revolute">
        <parent link="${prefix}_ezgripper_palm_link"/>
        <child link="${prefix}_ezgripper_finger_L1_${postfix}"/>
        <!-- Flip the fingers by adding 180 degrees (pi) to the roll -->
        <origin xyz="0.0595 ${reflectY*0.03} 0" rpy="${1.5708 * reflectR + 3.14159} 0 0"/>
        <axis xyz="0 1 0"/>
        <limit lower="-1.57075" upper="0.27" effort="1" velocity="3.67"/>
        <xacro:if value="${mimic_test}">
                <mimic joint="${prefix}_ezgripper_knuckle_palm_L1_1"/>
        </xacro:if>
    </joint>
</xacro:macro>
```

## Results Table

| Test Combination | Result | Notes |
|------------------|--------|-------|
| PK-1 + KF-1 | Testing | Original configuration |
| PK-1 + KF-2 | Pending | |
| PK-1 + KF-3 | Pending | |
| PK-1 + KF-4 | Pending | |
| PK-2 + KF-1 | Pending | |
| PK-2 + KF-2 | Pending | |
| PK-3 + KF-1 | Pending | |
| PK-3 + KF-2 | Pending | |
| PK-4 + KF-1 | Pending | |
| PK-4 + KF-2 | Pending | |

## Implementation Examples

Here are examples of how to implement some of these test configurations:

### Example 1: PK-1 + KF-2 (Original palm to knuckle, 180° Z rotation for knuckle to finger)

```python
# Palm to Knuckle transforms (original)
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=0.0595, y=0.03, z=0.0,
    roll=1.5708, pitch=0.0, yaw=0.0
)

# Knuckle to Finger transforms (180° Z rotation)
self.publish_static_transform(
    parent_frame=f'{prefix}_knuckle_palm_L1_1',
    child_frame=f'{prefix}_finger_L1_1',
    x=0.0, y=0.0, z=0.0,
    roll=0.0, pitch=0.0, yaw=3.14159
)
```

### Example 2: PK-2 + KF-1 (180° Z rotation for palm to knuckle, original knuckle to finger)

```python
# Palm to Knuckle transforms (180° Z rotation)
self.publish_static_transform(
    parent_frame=f'{prefix}_palm_link',
    child_frame=f'{prefix}_knuckle_palm_L1_1',
    x=0.0595, y=0.03, z=0.0,
    roll=1.5708, pitch=0.0, yaw=3.14159
)

# Knuckle to Finger transforms (original)
self.publish_static_transform(
    parent_frame=f'{prefix}_knuckle_palm_L1_1',
    child_frame=f'{prefix}_finger_L1_1',
    x=0.0, y=0.0, z=0.0,
    roll=0.0, pitch=0.0, yaw=0.0
)
```

## Conclusion

After testing all combinations, we'll identify the correct transform configuration that ensures the fingers are properly oriented in the triple gripper setup.
