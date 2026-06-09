# RB-VOGUI + UR Simulation Setup

This package is a lightweight integration point for early ROS 2 print-path following
simulation with a Robotnik RB-VOGUI-class mobile base and a UR arm.

It intentionally does not vendor third-party source code. Import the external public
simulation repositories with `vcs` into a workspace when you need to run the simulation.
Generic additive-manufacturing application logic remains in
`match_additive_manufacturing_ros2`.

## Sources

Robotnik simulation stack:

- Repository: `https://github.com/RobotnikAutomation/robotnik_simulation`
- Branch: `jazzy-devel`
- Includes Gazebo/Ignition launch assets for Robotnik platforms.
- Documents RB-VOGUI models `rbvogui` and `rbvogui_plus`.
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

Complete bringup:

```bash
ros2 launch robotnik_simulation_bringup bringup_complete.launch.py \
  robot_model:=rbvogui_plus \
  use_gui:=true \
  use_rviz:=false
```

Manual empty-world flow:

```bash
ros2 launch robotnik_gazebo_ignition spawn_world.launch.py world:=empty gui:=true

ros2 launch robotnik_gazebo_ignition spawn_robot.launch.py \
  robot_id:=robot \
  robot:=rbvogui \
  robot_model:=rbvogui_plus \
  arm_type:=ur5e \
  x:=0.0 y:=0.0 z:=0.1 \
  run_rviz:=false \
  use_sim_time:=true \
  low_performance_simulation:=true
```

The imported `rbvogui_plus` description includes the UR arm and accepts `arm_type:=ur5e`.

## Runtime Validation Status

Validation on ROS 2 Jazzy on June 9, 2026 established:

- Gazebo creates the `rbvogui_plus` entity with the UR5e arm.
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
binary or source checkout is therefore required before adding pose bridges or
claiming the AM demo is operational.

## Topic Discovery Procedure

After the simulator starts:

```bash
ros2 topic list | sort
ros2 topic info /robot/robotnik_base_control/cmd_vel -v
ros2 topic info /robot/robotnik_base_control/cmd_vel_unstamped -v
ros2 topic list | grep -E 'pose|odom|tf|joint|tool|tcp'
ros2 run tf2_ros tf2_echo robot/odom robot/base_link
```

Expected command topics from Robotnik docs:

- `/robot/robotnik_base_control/cmd_vel`: `geometry_msgs/msg/TwistStamped`
- `/robot/robotnik_base_control/cmd_vel_unstamped`: `geometry_msgs/msg/Twist`

These topic names are documented expectations, not runtime-verified interfaces while
the released base controller crashes. The generic AM follower should start with the
unstamped `Twist` command topic after a compatible controller is available.

## Pose Topic Contract For AM Nodes

The AM application packages expect external pose topics:

- Base pose: `geometry_msgs/msg/PoseStamped`, example `/robot_pose`
- TCP/nozzle pose: `geometry_msgs/msg/PoseStamped`, example `/current_tcp_pose`

Robotnik simulation may expose pose through odometry and TF rather than exactly these
topic names. Add small platform-side bridge/publisher nodes later if needed. Do not put
Robotnik-specific pose extraction inside generic AM packages.

## Next Checks

1. Obtain or build a Jazzy-compatible `robotnik_controllers` implementation.
2. Confirm that all three controllers remain active.
3. Record the exact base odometry topic and TF chain.
4. Record the exact TCP/nozzle TF chain.
5. Confirm lateral velocity on the unstamped `Twist` command topic.
6. Add only the minimal platform bridge nodes needed to publish `/robot_pose` and
   `/current_tcp_pose` for generic AM consumers.
