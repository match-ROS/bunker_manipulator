#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.time import Time


class TrackedCommandConverter(Node):
    """Convert the existing stamped Bunker command API to Gazebo track commands."""

    def __init__(self) -> None:
        super().__init__('tracked_command_converter')
        self.declare_parameter('input_topic', '/diff_drive_controller/cmd_vel')
        self.declare_parameter('output_topic', '/bunker/tracked_cmd_vel')
        self.declare_parameter('invert_angular_z', True)
        self.declare_parameter('command_timeout', 0.5)

        input_topic = str(self.get_parameter('input_topic').value)
        output_topic = str(self.get_parameter('output_topic').value)
        self.invert_angular_z = bool(self.get_parameter('invert_angular_z').value)
        self.command_timeout = max(0.0, float(self.get_parameter('command_timeout').value))
        self.last_command_time: Time | None = None
        self.stopped_for_timeout = True
        self.publisher = self.create_publisher(Twist, output_topic, 10)
        self.create_subscription(TwistStamped, input_topic, self._command_cb, 10)
        self.create_timer(0.1, self._timeout_cb)
        self.get_logger().info(
            f'Converting TwistStamped commands from {input_topic} to Twist on {output_topic}; '
            f'invert_angular_z={self.invert_angular_z}, timeout={self.command_timeout:.2f}s.'
        )

    def _command_cb(self, msg: TwistStamped) -> None:
        command = Twist()
        command.linear = msg.twist.linear
        command.angular = msg.twist.angular
        if self.invert_angular_z:
            command.angular.z = -command.angular.z
        self.publisher.publish(command)
        self.last_command_time = self.get_clock().now()
        self.stopped_for_timeout = False

    def _timeout_cb(self) -> None:
        if self.command_timeout <= 0.0 or self.last_command_time is None:
            return
        age = (self.get_clock().now() - self.last_command_time).nanoseconds / 1e9
        if age > self.command_timeout and not self.stopped_for_timeout:
            self.publisher.publish(Twist())
            self.stopped_for_timeout = True
            self.get_logger().warn('Tracked command timed out; publishing zero velocity.')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TrackedCommandConverter()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.publisher.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
