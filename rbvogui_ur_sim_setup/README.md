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
  x:=0.0 y:=0.0 z:=0.0 \
  run_rviz:=false
```

If `rbvogui_plus` does not include the desired UR variant in the imported Robotnik
description version, use this branch only as the mobile-base simulation baseline and
add a separate custom mobile-manipulator xacro in a later, platform-specific branch.

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

The generic AM follower should start with the unstamped `Twist` command topic unless the
active controller only accepts `TwistStamped`.

## Pose Topic Contract For AM Nodes

The AM application packages expect external pose topics:

- Base pose: `geometry_msgs/msg/PoseStamped`, example `/robot_pose`
- TCP/nozzle pose: `geometry_msgs/msg/PoseStamped`, example `/current_tcp_pose`

Robotnik simulation may expose pose through odometry and TF rather than exactly these
topic names. Add small platform-side bridge/publisher nodes later if needed. Do not put
Robotnik-specific pose extraction inside generic AM packages.

## Next Checks

1. Verify whether `rbvogui_plus` includes the UR arm required for the print-path demo.
2. Record the exact base pose topic or TF chain from the running simulator.
3. Record the exact TCP/nozzle pose topic or TF chain from the running simulator.
4. Confirm whether lateral velocity is accepted on the unstamped `Twist` command topic.
5. Add only the minimal platform bridge nodes needed to publish `/robot_pose` and
   `/current_tcp_pose` for generic AM consumers.
