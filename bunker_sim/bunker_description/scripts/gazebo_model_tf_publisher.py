#!/usr/bin/env python3
from typing import Optional

import rclpy
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer, TransformBroadcaster, TransformException, TransformListener
from tf_transformations import (
    inverse_matrix,
    quaternion_from_matrix,
    quaternion_matrix,
    translation_from_matrix,
    translation_matrix,
)


class GazeboModelTfPublisher(Node):
    def __init__(self) -> None:
        super().__init__('gazebo_model_tf_publisher')
        self.declare_parameter('gazebo_tf_topic', '/world/empty/dynamic_pose/info')
        self.declare_parameter('robot_pose_topic', '/robot_pose')
        self.declare_parameter('model_name', 'bunker')
        self.declare_parameter('world_frame', 'map')
        self.declare_parameter('robot_base_frame', 'base_footprint')
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('localization_source', 'gazebo')
        self.declare_parameter('publish_robot_pose', True)
        self.declare_parameter('use_first_unnamed_pose', True)

        self.model_name = str(self.get_parameter('model_name').value)
        self.world_frame = str(self.get_parameter('world_frame').value)
        self.robot_base_frame = str(self.get_parameter('robot_base_frame').value)
        self.odom_frame = str(self.get_parameter('odom_frame').value)
        self.localization_source = str(
            self.get_parameter('localization_source').value
        ).strip().lower()
        self.publish_robot_pose = bool(self.get_parameter('publish_robot_pose').value)
        self.use_first_unnamed_pose = bool(self.get_parameter('use_first_unnamed_pose').value)

        self.tf_broadcaster = TransformBroadcaster(self)
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.pose_pub = self.create_publisher(
            PoseStamped,
            str(self.get_parameter('robot_pose_topic').value),
            10,
        )

        if self.localization_source != 'odom':
            self.create_subscription(
                TFMessage,
                str(self.get_parameter('gazebo_tf_topic').value),
                self._gazebo_tf_cb,
                10,
            )
        self.create_subscription(
            Odometry,
            str(self.get_parameter('odom_topic').value),
            self._odom_cb,
            10,
        )
        if self.localization_source != 'odom':
            self.create_subscription(PoseStamped, 'pose', self._pose_cb, 10)
        self.get_logger().info(
            f"Publishing {self.world_frame} -> {self.odom_frame} localization from "
            f"{self.localization_source}."
        )

    def _gazebo_tf_cb(self, msg: TFMessage) -> None:
        if self.localization_source == 'odom':
            return
        selected = self._select_model_transform(msg)
        if selected is None:
            return
        self._publish_transform(selected)

    def _select_model_transform(self, msg: TFMessage) -> Optional[TransformStamped]:
        model_suffix = f'/{self.model_name}'
        for transform in msg.transforms:
            child_frame = transform.child_frame_id.strip('/')
            if child_frame == self.model_name or child_frame.endswith(model_suffix):
                return transform
        if self.use_first_unnamed_pose and msg.transforms:
            first = msg.transforms[0]
            if not first.child_frame_id.strip():
                return first
        return None

    def _odom_cb(self, msg: Odometry) -> None:
        if self.localization_source != 'odom':
            return
        stamp = self.get_clock().now().to_msg()
        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = self.odom_frame
        transform.child_frame_id = self.robot_base_frame
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = msg.pose.pose.position.z
        transform.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(transform)
        self._publish_robot_pose(transform, stamp)

        if self.world_frame != self.odom_frame:
            world_to_odom = TransformStamped()
            world_to_odom.header.stamp = stamp
            world_to_odom.header.frame_id = self.world_frame
            world_to_odom.child_frame_id = self.odom_frame
            world_to_odom.transform.rotation.w = 1.0
            self.tf_broadcaster.sendTransform(world_to_odom)

    def _pose_cb(self, msg: PoseStamped) -> None:
        transform = TransformStamped()
        transform.header = msg.header
        transform.child_frame_id = self.robot_base_frame
        transform.transform.translation.x = msg.pose.position.x
        transform.transform.translation.y = msg.pose.position.y
        transform.transform.translation.z = msg.pose.position.z
        transform.transform.rotation = msg.pose.orientation
        self._publish_transform(transform)

    def _publish_transform(self, transform: TransformStamped) -> None:
        stamp = self._stamp_or_now(transform)
        self._publish_robot_pose(transform, stamp)

        try:
            odom_to_base = self.buffer.lookup_transform(
                self.odom_frame,
                self.robot_base_frame,
                rclpy.time.Time(),
            )
        except TransformException as exc:
            self.get_logger().warn(
                f"Waiting for TF {self.odom_frame} <- {self.robot_base_frame}: {exc}",
                throttle_duration_sec=2.0,
            )
            return

        world_to_base = self._matrix_from_transform(transform)
        odom_to_base_matrix = self._matrix_from_transform(odom_to_base)
        world_to_odom = world_to_base @ inverse_matrix(odom_to_base_matrix)

        out = TransformStamped()
        out.header.stamp = stamp
        out.header.frame_id = self.world_frame
        out.child_frame_id = self.odom_frame
        self._fill_transform_from_matrix(out, world_to_odom)
        self.tf_broadcaster.sendTransform(out)

    def _stamp_or_now(self, transform: TransformStamped):
        return self.get_clock().now().to_msg()

    def _publish_robot_pose(self, transform: TransformStamped, stamp) -> None:
        if not self.publish_robot_pose:
            return
        pose = PoseStamped()
        pose.header.stamp = stamp
        pose.header.frame_id = self.world_frame
        pose.pose.position.x = transform.transform.translation.x
        pose.pose.position.y = transform.transform.translation.y
        pose.pose.position.z = transform.transform.translation.z
        pose.pose.orientation = transform.transform.rotation
        self.pose_pub.publish(pose)

    @staticmethod
    def _matrix_from_transform(transform: TransformStamped):
        translation = transform.transform.translation
        rotation = transform.transform.rotation
        matrix = translation_matrix([translation.x, translation.y, translation.z])
        matrix = matrix @ quaternion_matrix([rotation.x, rotation.y, rotation.z, rotation.w])
        return matrix

    @staticmethod
    def _fill_transform_from_matrix(transform: TransformStamped, matrix) -> None:
        translation = translation_from_matrix(matrix)
        rotation = quaternion_from_matrix(matrix)
        transform.transform.translation.x = float(translation[0])
        transform.transform.translation.y = float(translation[1])
        transform.transform.translation.z = float(translation[2])
        transform.transform.rotation.x = float(rotation[0])
        transform.transform.rotation.y = float(rotation[1])
        transform.transform.rotation.z = float(rotation[2])
        transform.transform.rotation.w = float(rotation[3])


def main(args=None) -> None:
    rclpy.init(args=args)
    node: Optional[GazeboModelTfPublisher] = None
    try:
        node = GazeboModelTfPublisher()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
