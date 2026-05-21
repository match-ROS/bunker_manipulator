# Robot Simulation Setup

## Start Simulation
Um die Simulation zu starten (mit dem funktionierenden Controller-Fix):
```bash
source install/setup.bash
ros2 launch my_robot_description spawn_with_controllers.launch.py
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
