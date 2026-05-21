#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, TwistStamped


class CmdVelRelay(Node):
    """Relays /cmd_vel (Twist) to /diff_drive_controller/cmd_vel (TwistStamped)."""

    def __init__(self) -> None:
        super().__init__('cmd_vel_to_diff_drive_twist_stamped')

        self.declare_parameter('in_topic', '/cmd_vel')
        self.declare_parameter('out_topic', '/diff_drive_controller/cmd_vel')
        self.declare_parameter('frame_id', 'base_link')

        in_topic = self.get_parameter('in_topic').get_parameter_value().string_value
        out_topic = self.get_parameter('out_topic').get_parameter_value().string_value

        self._frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        self._pub = self.create_publisher(TwistStamped, out_topic, 10)
        self._sub = self.create_subscription(Twist, in_topic, self._on_twist, 10)

        self.get_logger().info(f'Relaying {in_topic} (Twist) -> {out_topic} (TwistStamped), frame_id={self._frame_id}')

    def _on_twist(self, msg: Twist) -> None:
        stamped = TwistStamped()
        stamped.header.stamp = self.get_clock().now().to_msg()
        stamped.header.frame_id = self._frame_id
        stamped.twist = msg
        self._pub.publish(stamped)


def main() -> None:
    rclpy.init()
    node = CmdVelRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
