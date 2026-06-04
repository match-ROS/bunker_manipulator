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

The launch starts the platform `diff_drive_controller` and the standard simulated UR
`ur_joint_trajectory_controller`. The alternative UR controllers
`ur_scaled_joint_trajectory_controller`, `ur_forward_velocity_controller`, and
`ur_forward_position_controller` are loaded in the inactive state and can be selected with
`ros2 control switch_controllers`.

## Steuerung (Teleop)
Um den Roboter zu steuern (Fix für TwistStamped ist hier wichtig):
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap cmd_vel:=/diff_drive_controller/cmd_vel --param stamped:=true
```

## Notizen
- Der `controller_manager` ist unter `/controller_manager` erreichbar.
- Der Roboter benötigt `TwistStamped` Nachrichten.
- Lenken funktioniert aktuell noch nicht 100%ig (TODO).
