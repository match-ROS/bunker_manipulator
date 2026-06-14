# Bunker Simple Trajectory Follower

This checkpoint adapts the generic ROS 2 `base_trajectory_follower/simple_base_follower`
to the current Bunker + UR simulation interface. It does not add a Bunker-specific
controller.

## Files

- `bunker_description/config/bunker_simple_base_follower.yaml`
- `bunker_description/launch/bunker_path_following_demo.launch.py`

The launch starts:

- `parse_paths/test_path_generator`
- `base_trajectory_follower/simple_base_follower`
- optionally `bunker_description/spawn_with_controllers.launch.py`

## Bunker Defaults

The current Bunker simulation uses a differential-drive controller, so the follower
configuration disables lateral velocity:

- `max_vy: 0.0`
- `kp_y: 0.0`
- `output_stamped: true`
- `cmd_vel_topic: /diff_drive_controller/cmd_vel`
- `robot_pose_topic: /robot_pose`
- `path_frame: map`
- `publish_once: true`

Runtime validation showed that the current Jazzy `diff_drive_controller` subscribes
to `geometry_msgs/msg/TwistStamped` on `/diff_drive_controller/cmd_vel`. A short
stamped command moved `/robot_pose.x` from about `-0.0008` to `0.3427`.

The full default demo was also validated: the 1 m line path published on
`/bunker_base_path` in frame `map`, the follower reported `goal reached`,
`/robot_pose.x` reached about `0.94`, and `/diff_drive_controller/cmd_vel` returned
to a zero `TwistStamped`.

## Run

Start the simulator separately:

```bash
ros2 launch bunker_description spawn_with_controllers.launch.py
```

Then start the simple path demo:

```bash
ros2 launch bunker_description bunker_path_following_demo.launch.py
```

Or let the demo include the simulator:

```bash
ros2 launch bunker_description bunker_path_following_demo.launch.py launch_sim:=true
```

If the simulator pose frame changes, keep the path in the same frame:

```bash
ros2 launch bunker_description bunker_path_following_demo.launch.py \
  path_frame:=<pose_frame>
```

## Runtime Checks

Before allowing the robot to move, confirm the controller and topic contracts:

```bash
ros2 control list_controllers --controller-manager /controller_manager
ros2 topic info /robot_pose -v
ros2 topic info /diff_drive_controller/cmd_vel -v
ros2 topic echo /bunker_base_path --once
```

Expected first-pass behavior:

- `/robot_pose` is `geometry_msgs/msg/PoseStamped`;
- the active base command topic accepts `geometry_msgs/msg/TwistStamped`;
- published commands have `linear.y == 0.0`;
- the default path is a short straight line in `map`.
- the fixed path is published once with transient-local QoS.

Keep more complex paths for later tests, after the straight-line baseline remains
stable across repeated runs.
