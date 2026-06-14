# Robot Simulation Setup

## Dependencies

Install released ROS Jazzy dependencies with:

```bash
rosdep install --from-paths src --ignore-src -r -y
```

The official `ur_description` and `ur_simulation_gz` binaries are used by default. To build the
pinned official GitHub sources instead, import them explicitly:

```bash
vcs import src < src/bunker_manipulator/bunker_sim/dependencies.repos
```

## Robot Descriptions

The `bunker_description` package provides three Bunker variants:

- `bunker.xacro`: mobile Bunker platform without a robot arm
- `bunkeranka.xacro`: Bunker platform with the Franka arm
- `bunkur.xacro`: Bunker platform with a Universal Robots arm

`bunkur.xacro` uses a UR10e by default. Select another supported UR model with
the `ur_type` xacro argument, for example:

```bash
xacro "$(ros2 pkg prefix bunker_description)/urdf/bunkur.xacro" ur_type:=ur5e
```

## Start Simulation
Um die Simulation zu starten (mit dem funktionierenden Controller-Fix):
```bash
source install/setup.bash
ros2 launch bunker_description spawn_with_controllers.launch.py
```

Start the simulation together with a working RViz configuration:

```bash
ros2 launch bunker_description spawn_with_controllers.launch.py launch_rviz:=true
```

Run server-only Gazebo for runtime checks:

```bash
ros2 launch bunker_description spawn_with_controllers.launch.py headless:=true
```

Or start RViz in another sourced terminal after the simulation is running:

```bash
ros2 launch bunker_description view_robot.launch.py
```

When configuring RViz manually, use `base_footprint` as the Fixed Frame. For the RobotModel
display, select `/robot_description` and set its durability policy to `Transient Local`.
Do not add the MoveIt `MotionPlanning` display unless a matching MoveIt configuration and
`move_group` are running; it requires the separate `robot_description_semantic` SRDF.

If a ROS CLI command such as `ros2 param list` remains stuck after terminated simulations,
restart its discovery daemon:

```bash
ros2 daemon stop
ros2 daemon start
```

The launch starts the platform `diff_drive_controller` and the standard simulated UR
`ur_joint_trajectory_controller`. The alternative UR controllers
`ur_scaled_joint_trajectory_controller`, `ur_forward_velocity_controller`, and
`ur_forward_position_controller` are loaded in the inactive state and can be selected with
`ros2 control switch_controllers`.

To test the UR velocity controller, switch away from the trajectory controller first:

```bash
ros2 control switch_controllers \
  --controller-manager /controller_manager \
  --deactivate ur_joint_trajectory_controller \
  --activate ur_forward_velocity_controller

ros2 topic pub -r 200 /ur_forward_velocity_controller/commands \
  std_msgs/msg/Float64MultiArray "{data: [0.1, 0.0, 0.0, 0.0, 0.0, 0.0]}"
```

## Steuerung (Teleop)
Runtime validation showed that the current Jazzy `diff_drive_controller` subscribes
to stamped `geometry_msgs/msg/TwistStamped` on `/diff_drive_controller/cmd_vel`:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  --remap cmd_vel:=/diff_drive_controller/cmd_vel \
  --param stamped:=true
```

## Notizen
- Der `controller_manager` ist unter `/controller_manager` erreichbar.
- Der Standard-Launch verwendet stamped `TwistStamped` Nachrichten.
- Lenken funktioniert aktuell noch nicht 100%ig (TODO).
