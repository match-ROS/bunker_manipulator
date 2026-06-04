# Robot Simulation Setup

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

## Steuerung (Teleop)
Um den Roboter zu steuern (Fix für TwistStamped ist hier wichtig):
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap cmd_vel:=/diff_drive_controller/cmd_vel --param stamped:=true
```

## Notizen
- Der `controller_manager` läuft im Namespace `/controller_manager_node`.
- Der Roboter benötigt `TwistStamped` Nachrichten.
- Lenken funktioniert aktuell noch nicht 100%ig (TODO).
