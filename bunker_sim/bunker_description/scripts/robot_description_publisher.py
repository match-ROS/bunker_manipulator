#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from std_msgs.msg import String


class RobotDescriptionPublisher(Node):
    def __init__(self):
        super().__init__('robot_description_publisher')
        # QoS compatible with parameter event publishers (transient local)
        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
        )
        self.pub = self.create_publisher(String, 'robot_description', qos)
        # declare and get parameter
        self.declare_parameter('robot_description', '')
        content = self.get_parameter('robot_description').get_parameter_value().string_value
        if not content:
            self.get_logger().warn('robot_description parameter is empty')
        msg = String()
        msg.data = content
        # publish immediately and periodically in case of late-joiners
        self.pub.publish(msg)
        self.timer = self.create_timer(1.0, lambda: self.pub.publish(msg))


def main():
    rclpy.init()
    node = RobotDescriptionPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
