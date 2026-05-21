# controllers_ros2

This package provides the `jparse_velocity_controller` ROS 2 node.

The node subscribes to:
- `geometry_msgs/msg/TwistStamped` commands
- `sensor_msgs/msg/JointState` feedback
- the robot description on `robot_description_topic`

It computes joint velocity commands for a KDL chain using Eigen and publishes:
- joint velocity commands as `std_msgs/msg/Float64MultiArray`
- singular value diagnostics
- debug twist diagnostics

## Dependencies

This package uses:
- `ament_cmake`
- `rclcpp`
- `geometry_msgs`
- `sensor_msgs`
- `std_msgs`
- `kdl_parser`
- `orocos_kdl`
- `Eigen3`

## Build

From the workspace root:

```bash
colcon build --packages-select controllers_ros2
```

## Run

After sourcing your workspace, run the executable directly:

```bash
ros2 run controllers_ros2 jparse_velocity_controller
```

To launch the controller with the bunkur robot defaults, use:

```bash
ros2 launch controllers_ros2 bunkur_ur_velocity_controller.launch.py
```

To switch to simulation time, pass `sim:=true`:

```bash
ros2 launch controllers_ros2 bunkur_ur_velocity_controller.launch.py sim:=true
```

This launch file uses:
- `robot_name:=bunkur`
- `arm:=ur`
- `base_link:=bunkur/base_link`
- `tip_link:=bunkur/ur/tool0`
- `use_sim_time:=false` unless `sim:=true` is set

You can override any of the declared launch arguments, including topic names and controller tuning parameters.

The controller still expects a robot description to be published on the configured `robot_description_topic` in both modes.
If your hardware has a lift axis or another non-arm joint between the mobile base and the arm, the controller will include it if it lies on the KDL chain between `base_link` and `tip_link`. In that case the commanded joint order follows the chain order. If you want to exclude the lift axis, set `command_joint_names` explicitly so only the joints you want are written to the command topic.

## Notes

The package currently contains a single C++ controller node in `src/jparse_velocity_controller.cpp` and one launch file in `launch/bunkur_ur_velocity_controller.launch.py`.