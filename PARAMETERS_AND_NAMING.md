# EZGripper ROS2 Parameters and Naming Conventions

This document provides a comprehensive overview of all hierarchical parameters and naming conventions used in the EZGripper ROS2 package, including xacros, launch files, and other related files.

## Recent Updates

### Fixed Issues
- **Prefix Parameter**: The `prefix` parameter is now properly defined and passed in all URDF files. It is defined as a property in standalone files to ensure it's accessible in all included files.
- **Material Definitions**: Material references now properly use the centralized definitions in `materials.urdf.xacro` to avoid duplicate material definitions. All materials are now namespaced with the `ezgripper_` prefix.
- **Simplified Naming Convention**: The system now uses a simplified naming convention without embedded numbering or position references.
- **Simplified Joint Inversion Logic**: The joint publisher now uses a consistent and simplified inversion rule that works for all gripper configurations (single, double, triple). Only joints with `L1_2` in their name are inverted, which aligns with the reflection parameters in the XACRO files.
- **Dynamic N-Gripper Support**: The system now dynamically handles any number of grippers (N) without special cases. Joint detection and naming are automatically determined from the TF tree.

## Table of Contents
- [URDF/Xacro Parameters](#urdfxacro-parameters)
- [Launch File Parameters](#launch-file-parameters)
- [TF Frame Naming Conventions](#tf-frame-naming-conventions)
- [Joint Naming Conventions](#joint-naming-conventions)
- [Link Naming Conventions](#link-naming-conventions)
- [Material and Color Conventions](#material-and-color-conventions)
- [Configuration Parameters](#configuration-parameters)
- [N-Gripper Configuration](#n-gripper-configuration)

## URDF/Xacro Parameters

### Common Xacro Parameters

| Parameter | Description | Used In | Default |
|-----------|-------------|---------|---------|
| `prefix` | Prefix for all joint and link names (e.g., "left_arm") | All xacro files | "" (empty string) |
| `parent_link` | Parent link to attach the gripper to | All gripper xacros | Required parameter |
| `*origin` | Block parameter for specifying origin (xyz, rpy) | All gripper xacros | Required parameter |
| `postfix` | Identifier for specific fingers (e.g., "1", "2") | Finger macros | Required parameter |
| `reflect` | Reflection parameter for finger orientation | Finger macros | Required parameter |
| `reflectY`, `reflectZ`, `reflectR` | Specific reflection parameters for joints | Joint macros | Required parameters |
| `mimic_test` | Whether a joint mimics another joint | Knuckle joint macros | `false` |

### Xacro Macros

| Macro Name | Description | Parameters |
|------------|-------------|------------|
| `ezgripper_single` | Main macro for a single gripper | `prefix`, `parent_link`, `*origin` |
| `ezgripper_palm` | Palm component of the gripper | `prefix`, `parent_link`, `*origin` |
| `ezgripper_finger_L1` | First finger link | `prefix`, `postfix`, `reflect` |
| `ezgripper_finger_L2` | Second finger link | `prefix`, `postfix`, `reflect` |
| `ezgripper_finger_pad` | Finger pad component | `prefix`, `postfix`, `reflect` |
| `ezgripper_knuckle_palm_L1` | Knuckle joint between palm and L1 | `prefix`, `postfix`, `reflectY`, `reflectZ`, `reflectR`, `mimic_test` |
| `ezgripper_knuckle_L1_L2` | Knuckle joint between L1 and L2 | `prefix`, `postfix`, `reflectY`, `reflectZ`, `reflectR` |
| `ezgripper_joint_finger_pad` | Joint for finger pad | `prefix`, `postfix`, `reflectY`, `reflectZ`, `reflectR` |
| `ezgripper_knuckle_palm_trans` | Transmission for Gazebo | `prefix`, `postfix` |
| `gazebo_knuckle_jsp` | Gazebo joint state publisher | `prefix` |

## Launch File Parameters

### Common Launch Parameters

| Parameter | Description | Used In | Default |
|-----------|-------------|---------|---------|
| `use_sim_time` | Use simulation time | All launch files | `false` |
| `enable_hardware` | Enable hardware control | Description launch files | `false` |
| `namespace` | Namespace for the gripper | All launch files | `ezgripper` |
| `prefix` | Prefix for joint names to match TF tree frame IDs | All launch files | Varies (e.g., `left_arm`) |
| `launch_joint_publisher` | Whether to launch the gripper joint publisher | Description launch files | `true` |
| `launch_robot_state_publisher` | Whether to launch robot state publisher | Description launch files | `true` |
| `launch_static_tf_publisher` | Whether to launch the static TF publisher | Description launch files | `true` |
| `output_topic` | Topic to publish joint states to | Joint publisher launch files | `/ezgripper/joint_states` |
| `rviz` | Whether to launch RViz | Description launch files | `false` |

### Launch File Hierarchy

1. **Top-level Launch Files**:
   - `ezgripper_single_description.launch.py`
   - `ezgripper_double_description.launch.py`
   - `ezgripper_triple_description.launch.py`
   - `ezgripper_single_integration.launch.py`
   - `ezgripper_double_integration.launch.py`
   - `ezgripper_triple_integration.launch.py`
   - `ezgripper_single_standalone.launch.py`
   - `ezgripper_double_standalone.launch.py`
   - `ezgripper_triple_standalone.launch.py`

2. **Component Launch Files** (included by top-level launch files):
   - `gripper_joint_publisher.launch.py`
   - `gripper_static_tf_publisher.launch.py`

## Gripper Naming Conventions for Different Robot Configurations

The EZGripper package supports various robot configurations with single or multiple arms, each with single or triple grippers. Below are the naming conventions for different configurations:

### Case 1: Single Arm with Single Gripper
- **Arm Prefix**: e.g., `right`
- **Joint Names**:
  - `right_ezgripper_knuckle_palm_L1_1`
  - `right_ezgripper_knuckle_palm_L1_2`
- **Control Topic**:
  - `/ezgripper/right/command`

### Case 2: Single Arm with Triple Gripper
- **Arm Prefix**: e.g., `right`
- **Gripper Prefixes**:
  - `right_1`
  - `right_2`
  - `right_3`
- **Joint Names**:
  - `right_1_ezgripper_knuckle_palm_L1_1`, `right_1_ezgripper_knuckle_palm_L1_2`
  - `right_2_ezgripper_knuckle_palm_L1_1`, `right_2_ezgripper_knuckle_palm_L1_2`
  - `right_3_ezgripper_knuckle_palm_L1_1`, `right_3_ezgripper_knuckle_palm_L1_2`
- **Control Topics**:
  - `/ezgripper/right_1/command`
  - `/ezgripper/right_2/command`
  - `/ezgripper/right_3/command`

### Case 3: Two Arms Each with Single Gripper
- **Arm Prefixes**: e.g., `left`, `right`
- **Joint Names**:
  - `left_ezgripper_knuckle_palm_L1_1`, `left_ezgripper_knuckle_palm_L1_2`
  - `right_ezgripper_knuckle_palm_L1_1`, `right_ezgripper_knuckle_palm_L1_2`
- **Control Topics**:
  - `/ezgripper/left/command`
  - `/ezgripper/right/command`

### Case 4: Two Arms - One with Single Gripper, One with Triple Gripper
- **Arm Prefixes**: e.g., `left`, `right`
- **Left Arm (Single Gripper)**:
  - **Joint Names**:
    - `left_ezgripper_knuckle_palm_L1_1`
    - `left_ezgripper_knuckle_palm_L1_2`
  - **Control Topic**:
    - `/ezgripper/left/command`
- **Right Arm (Triple Gripper)**:
  - **Gripper Prefixes**:
    - `right_1`
    - `right_2`
    - `right_3`
  - **Joint Names**:
    - `right_1_ezgripper_knuckle_palm_L1_1`, `right_1_ezgripper_knuckle_palm_L1_2`
    - `right_2_ezgripper_knuckle_palm_L1_1`, `right_2_ezgripper_knuckle_palm_L1_2`
    - `right_3_ezgripper_knuckle_palm_L1_1`, `right_3_ezgripper_knuckle_palm_L1_2`
  - **Control Topics**:
    - `/ezgripper/right_1/command`
    - `/ezgripper/right_2/command`
    - `/ezgripper/right_3/command`

### Important Notes
- Each gripper is independently controlled via its own topic
- Within each gripper, the L1_1 and L1_2 fingers are opposing and move in opposite directions
- For triple grippers, each palm (1, 2, 3) is independently controlled

## TF Frame Naming Conventions

The TF frames follow a hierarchical structure with the following pattern:

```
<prefix>_ezgripper_<component>_<identifier>
```

For triple grippers, the pattern includes a numeric identifier:

```
<prefix>_<num>_ezgripper_<component>_<identifier>
```

### Main TF Frames

| Frame Name Pattern | Description |
|-------------------|-------------|
| `<prefix>_ezgripper_palm_link` | The palm link of the gripper |
| `<prefix>_ezgripper_finger_L1_<finger_num>` | First link of finger (finger_num is typically 1, 2, or 3) |
| `<prefix>_ezgripper_finger_L2_<finger_num>` | Second link of finger |
| `<prefix>_ezgripper_finger_pad_<finger_num>` | Finger pad link |

## Joint Naming Conventions

Joints follow a similar naming convention:

```
<prefix>_ezgripper_<joint_type>_<identifier>
```

For triple grippers, the pattern includes a numeric identifier:

```
<prefix>_<num>_ezgripper_<joint_type>_<identifier>
```

### Main Joints

| Joint Name Pattern | Description | Type |
|-------------------|-------------|------|
| `<prefix>_ezgripper_to_parent` | Joint connecting gripper to parent link | `fixed` |
| `<prefix>_ezgripper_knuckle_palm_L1_<finger_num>` | Knuckle joint between palm and L1 | `revolute` |
| `<prefix>_ezgripper_knuckle_L1_L2_<finger_num>` | Joint between L1 and L2 | `fixed` |
| `<prefix>_ezgripper_joint_finger_pad_<finger_num>` | Joint for finger pad | `fixed` |

## Link Naming Conventions

Links follow this naming convention:

```
<prefix>_ezgripper_<component>_<identifier>
```

For triple grippers, the pattern includes a numeric identifier:

```
<prefix>_<num>_ezgripper_<component>_<identifier>
```

### Main Links

| Link Name Pattern | Description |
|-------------------|-------------|
| `<prefix>_ezgripper_palm_link` | The palm link |
| `<prefix>_ezgripper_finger_L1_<finger_num>` | First finger link |
| `<prefix>_ezgripper_finger_L2_<finger_num>` | Second finger link |
| `<prefix>_ezgripper_finger_pad_<finger_num>` | Finger pad link |

## Material and Color Conventions

### Material Definition and Usage

The EZGripper package uses a centralized approach for defining materials to ensure consistency across all components and to avoid duplicate material definitions. All materials are namespaced with the `ezgripper_` prefix to prevent conflicts with other packages.

#### Material File Structure

Materials are defined in the central file: `ezgripper_description/urdf/materials.urdf.xacro`

```xml
<!-- Material color properties defined as xacro properties -->
<xacro:property name="ezgripper_black_rgba" value="0.0 0.0 0.0 1.0" />
<xacro:property name="ezgripper_blue_rgba" value="0.0 0.0 0.8 1.0" />
<xacro:property name="ezgripper_grey_rgba" value="0.5 0.5 0.5 1.0" />
<xacro:property name="ezgripper_white_rgba" value="1.0 1.0 1.0 1.0" />

<!-- Material definitions provided through a macro -->
<xacro:macro name="define_ezgripper_materials">
  <material name="ezgripper_black">
    <color rgba="${ezgripper_black_rgba}"/>
  </material>
  
  <material name="ezgripper_blue">
    <color rgba="${ezgripper_blue_rgba}"/>
  </material>
  
  <material name="ezgripper_grey">
    <color rgba="${ezgripper_grey_rgba}"/>
  </material>
  
  <material name="ezgripper_white">
    <color rgba="${ezgripper_white_rgba}"/>
  </material>
</xacro:macro>
```

#### How to Use Materials in Component Files

1. **Include the materials file**:
   ```xml
   <xacro:include filename="$(find ezgripper_description)/urdf/materials.urdf.xacro" />
   ```

2. **Call the material definition macro**:
   ```xml
   <xacro:define_ezgripper_materials />
   ```

3. **Reference materials in visual elements**:
   ```xml
   <visual>
     <geometry>
       <mesh filename="package://ezgripper_description/meshes/visual/SAKE_Palm_IM.stl"/>
     </geometry>
     <material name="ezgripper_blue"/>
   </visual>
   ```

### Integration with Other Packages

When integrating the EZGripper with other packages like SCARA arm or MiniLift:

1. **Maintain Namespaced Materials**: Always use the namespaced material names (`ezgripper_black`, `ezgripper_blue`, etc.) to avoid conflicts.

2. **For SCARA Arm Integration**:
   - The SCARA arm should define its own materials with a different namespace prefix (e.g., `scara_blue`, `scara_grey`).
   - When including both packages, each component will use its own namespaced materials.

3. **For MiniLift Integration**:
   - Similar to SCARA arm, MiniLift should define its materials with a unique namespace prefix.
   - This prevents material definition conflicts in the combined URDF.

4. **Gazebo Material Mapping**:
   - For Gazebo simulation, map the namespaced materials to Gazebo materials:
     ```xml
     <gazebo reference="${prefix}_ezgripper_palm_link">
       <material>Gazebo/Blue</material>
     </gazebo>
     ```

### Custom Color Definitions

To customize colors for a specific integration:

1. Create a custom material property in your integration file:
   ```xml
   <xacro:property name="custom_ezgripper_blue_rgba" value="0.0 0.1 0.9 1.0" />
   ```

2. Override the standard material definition:
   ```xml
   <material name="ezgripper_blue">
     <color rgba="${custom_ezgripper_blue_rgba}"/>
   </material>
   ```

## Configuration Parameters

### Gripper Configurations

| Configuration | Description | Files |
|---------------|-------------|-------|
| Single Gripper | Standard single gripper | `ezgripper_single.urdf.xacro`, `ezgripper_single_mount.urdf.xacro` |
| Double Gripper | Two grippers mounted together | `ezgripper_double_with_mount.urdf.xacro`, `ezgripper_double_with_mount_standalone.urdf.xacro` |
| Triple Gripper | Three grippers mounted together | `ezgripper_triple_with_mount.urdf.xacro`, `ezgripper_triple_with_mount_standalone.urdf.xacro` |

### Mount Configurations

| Mount Type | Description | Files |
|------------|-------------|-------|
| Standard Mount | Standard mounting configuration | `ezgripper_single_mount.urdf.xacro` |
| SAKE Mount | SAKE-specific mounting | `SAKE_single_mount.urdf.xacro`, `SAKE_double_mount.urdf.xacro`, `SAKE_triple_mount.urdf.xacro` |

### Joint Limits and Physical Properties

| Parameter | Value | Description |
|-----------|-------|-------------|
| Knuckle Joint Limits | `lower="-1.57075" upper="0.27"` | Range of motion for knuckle joints |
| Effort Limit | `effort="1"` | Maximum effort for actuated joints |
| Velocity Limit | `velocity="3.67"` | Maximum velocity for actuated joints |

## Usage Examples

### Single Gripper Example

```xml
<xacro:ezgripper_single prefix="left_arm" parent_link="robot_base_link">
  <origin xyz="0 0 0" rpy="0 0 0"/>
</xacro:ezgripper_single>
```

### Launch File Example

```bash
ros2 launch ezgripper_description ezgripper_single_description.launch.py prefix:=left_arm namespace:=ezgripper
```

## N-Gripper Configuration

The EZGripper ROS2 package now supports dynamic detection and control of any number of grippers without special cases. This section describes how the system handles both standard single grippers and multiple gripper configurations.

### Gripper Identification Using Palm Links

The most reliable way to identify all grippers in the TF tree is to search for palm links with "ezgripper_palm_link" in their names. This approach works because:

1. The palm link name is immutable in the XACRO files - it's a fixed part of the gripper structure definition that doesn't change regardless of configuration.
2. The palm link serves as the fundamental reference point for each gripper in the TF tree.
3. The naming convention for palm links is consistent across all gripper configurations.

In the triple gripper configuration, the palm links are named:
- `gripper_1_ezgripper_palm_link`
- `gripper_2_ezgripper_palm_link`
- `gripper_3_ezgripper_palm_link`

These palm links are direct children of the `gripper_ezgripper_to_mount` link in the TF tree.

The gripper joint publisher uses this approach to reliably detect all grippers in the system by:
1. Getting all frames in the TF tree
2. Filtering for frames containing "ezgripper_palm_link"
3. Extracting the prefix (everything before "_ezgripper_palm_link")
4. Creating the appropriate joint names based on these prefixes

This method ensures that all grippers are correctly identified regardless of whether they're in a single, dual, or triple configuration.

### Dynamic Joint Detection

The joint publisher dynamically detects gripper configurations from the TF tree using the following approach:

1. **Standard Single Gripper Detection**: 
   - First, the system looks for standard single gripper frames (without a `gripper_N_` prefix)
   - It searches for frames containing `ezgripper_palm_link` that don't match the numbered pattern
   - The prefix is extracted from these frames (everything before `_ezgripper_palm_link`)

2. **Multiple Gripper Detection**: 
   - The system then scans for frames matching the pattern `gripper_N_ezgripper` where N is any number (1, 2, 3, ...)
   - Each unique prefix is identified as a separate gripper
   - This handles cases where multiple grippers are present in the system

3. **Finger Detection**: 
   - For each detected gripper prefix, the system checks for knuckle joints in the TF tree
   - If found, it uses those exact joint names
   - If not found, it creates joint names based on the finger patterns detected in the TF tree

4. **Joint Creation**: 
   - Joint names are created following the pattern `<prefix>_ezgripper_knuckle_palm_L1_<finger_num>` where:
   - `<prefix>` is the detected gripper prefix (standard prefix or `gripper_N`)
   - `<finger_num>` is the finger number (1, 2, 3, ...) detected in the TF tree

### Naming Conventions

#### Standard Single Gripper

For a standard single gripper configuration:

- **Gripper Prefix**: Any custom prefix (e.g., `robot_arm`, `manipulator`, etc.) or no prefix
- **TF Frames**: Frames follow the pattern `<prefix>_ezgripper_<component>`
- **Joint Names**: Joint names follow the pattern `<prefix>_ezgripper_knuckle_palm_L1_<finger_num>`

#### Multiple Grippers (N Grippers)

For configurations with N grippers, the following naming convention is used:

- **Gripper Prefixes**: `gripper_1`, `gripper_2`, `gripper_3`, ..., `gripper_N`
- **TF Frames**: Each gripper has its own set of TF frames prefixed with its gripper prefix
- **Joint Names**: Each gripper has its own set of joint names prefixed with its gripper prefix

### Debug and Verification

The debug script (`/home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/scripts/debug_ezgripper.sh`) has been enhanced to analyze both standard single gripper and N-gripper configurations:

1. It detects both standard and numbered gripper prefixes in the TF tree and joint states
2. It distinguishes between standard prefixes and numbered prefixes in the output
3. It counts the total number of grippers detected
4. It analyzes all L1_N joints for each gripper
5. It checks for mismatches between TF tree and joint states

To run the debug script:

```bash
/home/sake/linorobot2_ws/src/EZGripper_ros2/ezgripper_description/scripts/debug_ezgripper.sh
```

### Multiple Grippers Example

For double gripper:
```bash
ros2 launch ezgripper_description ezgripper_double_description.launch.py prefix:=dual_gripper namespace:=ezgripper
```

For triple gripper:
```bash
ros2 launch ezgripper_description ezgripper_triple_description.launch.py prefix:=triple_gripper namespace:=ezgripper
```

## Naming Convention

The EZGripper package uses a consistent naming convention that includes "ezgripper" in the component names for clarity and to prevent naming collisions with other robot components. The primary identifier for each gripper is its prefix, which can be set through launch file parameters.

### Double Gripper Configuration
For double grippers, the two grippers use numeric identifiers (1, 2) to maintain consistency with the physical arrangement:
- Gripper 1: Left position in the double assembly
- Gripper 2: Right position in the double assembly

### Triple Gripper Configuration
For triple grippers, the three grippers use numeric identifiers (1, 2, 3) to maintain consistency with the physical arrangement:
- Gripper 1: Left position in the triple assembly
- Gripper 2: Center position in the triple assembly
- Gripper 3: Right position in the triple assembly

Including "ezgripper" in the naming pattern provides several benefits:
1. Clearly identifies components as part of the EZGripper system
2. Prevents naming collisions with other robot components
3. Makes debugging and visualization easier
4. Maintains consistency with ROS conventions
