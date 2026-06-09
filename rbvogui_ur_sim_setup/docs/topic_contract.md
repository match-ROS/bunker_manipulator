# RB-VOGUI Topic Contract For AM Demos

The generic AM demo should connect to the Robotnik simulation through launch arguments,
not hardcoded topic names.

## Candidate Inputs

Base pose:

- Preferred AM topic: `/robot_pose`
- Candidate Robotnik sources to inspect:
  - `/robot/odom`
  - `/tf`
  - `/tf_static`

TCP/nozzle pose:

- Preferred AM topic: `/current_tcp_pose`
- Candidate Robotnik/UR sources to inspect:
  - `/tf`
  - `/tf_static`
  - UR tool frame transforms

## Candidate Outputs

Base command:

- Preferred first command topic: `/robot/robotnik_base_control/cmd_vel_unstamped`
- Type: `geometry_msgs/msg/Twist`
- Reason: generic base followers can publish x, y, and yaw velocity without
  platform-specific stamping.

Fallback command topic:

- Topic: `/robot/robotnik_base_control/cmd_vel`
- Type: `geometry_msgs/msg/TwistStamped`
- Use only if the active controller requires stamped messages.

## Generic Follower Parameters

The later `base_trajectory_follower` package should expose:

- `path_topic`
- `robot_pose_topic`
- `cmd_vel_topic`
- `cmd_vel_stamped`
- `base_frame`
- `world_frame`
- `lookahead_distance`
- `xy_goal_tolerance`
- `yaw_goal_tolerance`
- `max_vx`
- `max_vy`
- `max_wz`
- `stale_pose_timeout`
