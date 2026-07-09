# RB-VOGUI + UR Simulation Setup

This package is a lightweight integration point for early ROS 2 print-path following
simulation with the Robotnik RB-VOGUI-XL mobile base and a UR arm.

It intentionally does not vendor third-party source code. Import the external public
simulation repositories with `vcs` into a workspace when you need to run the simulation.
Generic additive-manufacturing application logic remains in
`match_additive_manufacturing_ros2`.

## Sources

Robotnik simulation stack:

- Repository: `https://github.com/RobotnikAutomation/robotnik_simulation`
- Branch: `jazzy-devel`
- Includes Gazebo/Ignition launch assets for Robotnik platforms.
- Documents RB-VOGUI-XL models `rbvogui_xl`.
- Command topics are documented as:
  - stamped: `/<robot_id>/robotnik_base_control/cmd_vel`
  - unstamped: `/<robot_id>/robotnik_base_control/cmd_vel_unstamped`

Optional standalone UR Gazebo simulation reference:

- Repository: `https://github.com/UniversalRobots/Universal_Robots_ROS2_GZ_Simulation`
- Branch: `ros2`
- Useful as a reference for UR simulation/controller behavior if Robotnik's mobile
  manipulator description is not sufficient.

## Import Dependencies

From the workspace root:

```bash
vcs import src < src/bunker_manipulator/rbvogui_ur_sim_setup/dependencies/rbvogui_simulation.jazzy.repos
```

The manifest imports only Robotnik repositories. Use the ROS Jazzy packages for
general dependencies such as `gz_ros2_control`; do not add a second source copy
unless a specific upstream fix requires it.

Optional UR standalone simulation reference:

```bash
vcs import src < src/bunker_manipulator/rbvogui_ur_sim_setup/dependencies/ur_simulation_gz.ros2.repos
```

Install dependencies and build:

```bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

`robotnik_controllers` requires the message libraries from the imported
`robotnik_interfaces` repository. For a minimal simulation build, make sure these
packages are built before starting Gazebo:

```bash
colcon build --symlink-install --packages-up-to robotnik_controllers_msgs
colcon build --symlink-install --packages-up-to robotnik_gazebo_ignition
source install/setup.bash
```

The Robotnik README also describes installing its prebuilt debs from
`robotnik_simulation/debs` when required by the simulation stack.

## Start Robotnik Simulation

Recommended validated flow:

```bash
ros2 launch rbvogui_ur_sim_setup rbvogui_ur_standard_control.launch.py gui:=false
```

This launch uses Robotnik's public RB-VOGUI body/wheel meshes and UR arm macros, but
it does not load the released `robotnik_controllers` base controller. Instead it
starts standard Jazzy joint-group controllers and a small platform-side swerve node:

- `/robot/robotnik_base_control/cmd_vel_unstamped`: `geometry_msgs/msg/Twist`
- `/robot_pose`: `geometry_msgs/msg/PoseStamped`
- `/current_tcp_pose`: `geometry_msgs/msg/PoseStamped`
- `/robot/steering_position_controller/commands`: steering joint position commands
- `/robot/wheel_velocity_controller/commands`: wheel joint velocity commands
- `/robot/lift_position_controller/commands`: Ewellix lift position command
- `/robot/joint_trajectory_controller`: UR arm trajectory controller
- `/robot/arm_forward_velocity_controller/commands`: UR arm joint velocity commands

The swerve node is intentionally platform-specific and lives in this setup package,
not in `match_additive_manufacturing_ros2`.

Complete bringup:

```bash
ros2 launch robotnik_simulation_bringup bringup_complete.launch.py \
  robot_model:=rbvogui_xl \
  use_gui:=true \
  use_rviz:=false
```

Robotnik upstream empty-world flow:

```bash
ros2 launch robotnik_gazebo_ignition spawn_world.launch.py world:=empty gui:=true

ros2 launch robotnik_gazebo_ignition spawn_robot.launch.py \
  robot_id:=robot \
  robot:=rbvogui_xl \
  robot_model:=rbvogui_xl \
  arm_type:=ur20 \
  x:=0.0 y:=0.0 z:=0.1 \
  run_rviz:=false \
  use_sim_time:=true \
  low_performance_simulation:=true
```

The local description mirrors the copied real-robot setup: RB-VOGUI-XL base geometry,
285 mm wheels, an Ewellix 900 mm lift at the real mounting offset, and a UR20 mounted
on the lift link. The copied real-robot bringup sets `ROBOT_DEVICES_LIFT_1_MODEL=none`,
but this simulation exposes `robot_lift_joint` through a local standard position
controller for testing.
The retracted lift mount is currently estimated at about 0.35 m above the chassis
top plate.
The 285 mm wheel Xacros and rubber-wheel mesh are stored in this package so the
external `robotnik_description` checkout can stay unchanged.

## Runtime Validation Status

Validation on ROS 2 Jazzy on June 10, 2026 established:

- Gazebo creates the `rbvogui_xl`-class entity with the UR20 arm.
- The base and arm hardware interfaces initialize.
- `joint_state_broadcaster` loads and activates.
- The released `robotnik_controllers` binary requires
  `robotnik_controllers_msgs` to be built from the imported source.
- After that library is available, `robotnik_base_control` loads and activates, but
  its first update throws `std::bad_variant_access`. Controller deactivation then
  frees an invalid pointer and terminates Gazebo.
- Because Gazebo terminates immediately, the base command, odometry, and complete
  UR controller/TF interfaces cannot yet be validated at runtime.

The failing binary is `ros-jazzy-robotnik-controllers` version
`1.0.0-20250407.075635-7bed613`. The upstream
`RobotnikAutomation/robotnik_controllers` repository is referenced by Robotnik's
interface documentation but is not anonymously accessible. A compatible controller
binary or source checkout is required before using Robotnik's controller directly.

The local standard-controller launch was validated as a workaround:

- The local standard-controller launch starts these controllers:
  - `joint_state_broadcaster`
  - `steering_position_controller`
  - `wheel_velocity_controller`
  - `lift_position_controller`
  - `joint_trajectory_controller`
  - `arm_forward_velocity_controller` loaded inactive for later path following
- A command on `/robot/robotnik_base_control/cmd_vel_unstamped` with
  `linear.x=0.15` and `linear.y=0.10` moved the Gazebo model pose from near
  `(0.0, 0.0)` to about `(0.375, 0.225)`.
- Steering joints settled near `0.588 rad`, matching `atan2(0.10, 0.15)`.
- `/robot_pose` publishes `geometry_msgs/msg/PoseStamped` from Gazebo's
  `/world/robotnik_simple/dynamic_pose/info` stream. A later validation run moved
  `/robot_pose` from near `(0.0, 0.0)` to about `(0.285, 0.165)` after a short
  x/y command.
- The same Gazebo model-pose stream publishes the TF root
  `map -> robot_base_footprint`, which allows the generic
  `current_pose_from_tf` node to publish `/current_tcp_pose` for
  `robot_arm_tool0`.

The Gazebo `Pose_V -> TFMessage` bridge does not preserve entity names in this
environment. The local pose publisher therefore uses transform index `0`, which was
verified to be the `robot` model pose in `/world/robotnik_simple/dynamic_pose/info`.

## Topic Discovery Procedure

After the simulator starts:

```bash
ros2 topic list | sort
ros2 topic info /robot/robotnik_base_control/cmd_vel_unstamped -v
ros2 topic echo /robot_pose --once
ros2 topic echo /current_tcp_pose --once
ros2 control list_controllers --controller-manager /robot/controller_manager
ros2 control list_hardware_interfaces --controller-manager /robot/controller_manager
ros2 topic echo /robot/arm_forward_velocity_controller/commands --once
ros2 topic list | grep -E 'pose|odom|tf|joint|tool|tcp'
gz topic -e -t /world/robotnik_simple/dynamic_pose/info --json-output | grep '"name":"robot"'
```

Expected command topics from Robotnik docs:

- `/robot/robotnik_base_control/cmd_vel`: `geometry_msgs/msg/TwistStamped`
- `/robot/robotnik_base_control/cmd_vel_unstamped`: `geometry_msgs/msg/Twist`

The local standard-controller workaround accepts the same unstamped `Twist` topic as
its platform command input. The stamped Robotnik command topic is only expected when
using Robotnik's own base controller.

## Pose Topic Contract For AM Nodes

The AM application packages expect external pose topics:

- Base pose: `geometry_msgs/msg/PoseStamped`, example `/robot_pose`
- TCP/nozzle pose: `geometry_msgs/msg/PoseStamped`, example `/current_tcp_pose`

The validated model pose source is the Gazebo topic
`/world/robotnik_simple/dynamic_pose/info`. The launch bridges it through
`ros_gz_bridge` and publishes `/robot_pose` as `geometry_msgs/msg/PoseStamped`.
The same source is also broadcast as the TF transform
`map -> robot_base_footprint`, so `/current_tcp_pose` can be resolved
from the ROS robot-state TF tree to `robot_arm_tool0`.
Do not put Robotnik-specific pose extraction inside generic AM packages.

## Next Checks

1. Validate the TCP pose while executing an arm trajectory.
2. Decide whether later AM launches should consume `/current_tcp_pose` directly or
   remap it through scenario-specific topic names.
