# Bunker + UR Platform Adaptation Plan

This document records the current Bunker + UR simulation state and the missing pieces
needed before generic AM path-following nodes can be reused safely.

## Current Evidence

Simulation bringup:

- Package: `bunker_description`
- Main launch: `bunker_description/launch/spawn_with_controllers.launch.py`
- Robot model: `bunkur.xacro`
- Gazebo bridge:
  - `/clock`
  - `/world/empty/dynamic_pose/info`
- Model pose helper:
  - node: `gazebo_model_tf_publisher`
  - publishes `/robot_pose` as `geometry_msgs/msg/PoseStamped`
  - publishes `map -> odom` localization transform when `odom -> base_footprint` is available

Base controller:

- Controller: `diff_drive_controller`
- Config examples:
  - `bunker_description/config/test_controllers.yaml` (used by
    `spawn_with_controllers.launch.py` by default)
  - `bunker_description/config/bunker_controllers.yaml`
  - `bunker_description/config/diff_drive_controller.yaml`
- Current interface is differential-drive, not omnidirectional.
- Runtime validation on ROS 2 Jazzy showed the active controller subscribes to
  `geometry_msgs/msg/TwistStamped` on `/diff_drive_controller/cmd_vel`.
- The full default Bunker demo moved along the 1 m line path, reached about
  `/robot_pose.x=0.94`, reported `goal reached`, and returned the command topic
  to zero.

UR arm control:

- Launch: `controllers_ros2/launch/bunkur_ur_velocity_controller.launch.py`
- Node: `controllers_ros2/jparse_velocity_controller`
- Consumes `TwistStamped`, joint states, and robot description.
- Publishes joint velocity commands.
- `spawn_with_controllers.launch.py` loads:
  - active `ur_joint_trajectory_controller`
  - inactive `ur_forward_velocity_controller`
  - inactive `ur_forward_position_controller`

## Known Gaps

Base command contract:

- Active command topic: `/diff_drive_controller/cmd_vel`.
- Type: `geometry_msgs/msg/TwistStamped`.
- Confirm Bunker cannot use lateral `linear.y`; generic follower must disable or ignore y velocity
  for this platform.

Base pose contract:

- `/robot_pose` exists by design through `gazebo_model_tf_publisher`.
- Runtime-validated frame ID is `map`.
- Runtime-validated pose height is about `z=0.35`; the simple planar follower uses
  x/y/yaw only.
- Runtime-validated TF frame names:
  - `map`
  - `odom`
  - `base_footprint`

TCP/nozzle pose contract:

- Exact UR tool frame from TF is `ur_tool0`.
- Decide whether AM demos should consume `/current_tcp_pose` from
  `ur_trajectory_follower/current_pose_from_tf` or a platform-side publisher.
- TF resolves `map -> ur_tool0`.

Controller switching:

- Document the command needed to switch from `ur_joint_trajectory_controller` to
  `ur_forward_velocity_controller`.
- Confirm command order and joint names for the UR velocity controller.
- Confirm `jparse_velocity_controller` base/tip frame arguments for `bunkur.xacro`.

MoveIt:

- Do not require MoveIt for the simple path-following foundation.
- Add MoveIt later only if planning, collision checking, or semantic robot model is needed.
- Current TODO: identify whether a valid BunkUR SRDF and `move_group` launch exist.

## Adaptation Strategy

1. Keep `match_additive_manufacturing_ros2` generic.
2. Configure `base_trajectory_follower/simple_base_follower` for Bunker with:
   - `max_vy: 0.0`
   - `allow_reverse` decided by controller behavior
   - Bunker command topic `/diff_drive_controller/cmd_vel`
   - `output_stamped: true`
   - `robot_pose_topic: /robot_pose`
3. Use existing `current_pose_from_tf` for `/current_tcp_pose` if TF is reliable.
4. Add only platform-side launch/config overlays in `bunker_manipulator` for Bunker defaults.
   First-pass files now live in `bunker_description/config/bunker_simple_base_follower.yaml`
   and `bunker_description/launch/bunker_path_following_demo.launch.py`.
5. Do not port ROS 1 MiR follower complexity until the simple follower fails a documented test.

## Runtime Inspection Checklist

After launching:

```bash
ros2 launch bunker_description spawn_with_controllers.launch.py
ros2 control list_controllers --controller-manager /controller_manager
ros2 topic list | sort
ros2 topic info /robot_pose -v
ros2 topic info /diff_drive_controller/cmd_vel -v
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_ros tf2_echo map ur_tool0
```

Record:

- base command topic and message type, currently validated as
  `/diff_drive_controller/cmd_vel` with `geometry_msgs/msg/TwistStamped`
- whether `linear.y` is ignored or rejected
- exact TCP/tool frame
- exact base frame for Bunker follower config
- whether `/robot_pose` updates at the expected rate

## Useful Future Placeholders

The first-pass simple follower overlay exists and should be adjusted if the running
controller changes topic/type:

- `bunker_description/config/bunker_simple_base_follower.yaml`
- `bunker_description/launch/bunker_path_following_demo.launch.py`
- optional platform bridge for `/current_tcp_pose` if TF-based pose publishing is not enough
