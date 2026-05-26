from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.actions import Node


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument("sim", default_value="false"),
        DeclareLaunchArgument("robot_name", default_value="bunkur"),
        DeclareLaunchArgument("arm", default_value="ur"),
        DeclareLaunchArgument("base_link", default_value="base_link"),
        DeclareLaunchArgument("tip_link", default_value="tool0"),
        DeclareLaunchArgument("robot_description_topic", default_value="/robot_description"),
        DeclareLaunchArgument("twist_topic", default_value="~/twist_cmd"),
        DeclareLaunchArgument(
            "command_topic",
            default_value="/forward_velocity_controller/commands",
        ),
        DeclareLaunchArgument("joint_states_topic", default_value="/joint_states"),
        DeclareLaunchArgument(
            "singular_values_topic",
            default_value="/jparse_velocity_controller_ur/singular_values",
        ),
        DeclareLaunchArgument(
            "debug_twist_topic",
            default_value="/jparse_velocity_controller_ur/debug_twist",
        ),
        DeclareLaunchArgument("rate_hz", default_value="500.0"),
        DeclareLaunchArgument("command_timeout", default_value="0.12"),
        DeclareLaunchArgument("gamma", default_value="0.1"),
        DeclareLaunchArgument("singular_gain_position", default_value="1.0"),
        DeclareLaunchArgument("singular_gain_angular", default_value="1.0"),
        DeclareLaunchArgument("pinv_tolerance", default_value="1.0e-6"),
        DeclareLaunchArgument("max_joint_velocity", default_value="1.5"),
        DeclareLaunchArgument("max_cartesian_linear_velocity", default_value="0.25"),
        DeclareLaunchArgument("max_cartesian_angular_velocity", default_value="0.8"),
    ]

    controller_node = Node(
        package="controllers_ros2",
        executable="jparse_velocity_controller",
        output="screen",
        parameters=[
            {
                "use_sim_time": ParameterValue(LaunchConfiguration("sim"), value_type=bool),
                "robot_name": LaunchConfiguration("robot_name"),
                "arm": LaunchConfiguration("arm"),
                "base_link": LaunchConfiguration("base_link"),
                "tip_link": LaunchConfiguration("tip_link"),
                "robot_description_topic": LaunchConfiguration("robot_description_topic"),
                "twist_topic": LaunchConfiguration("twist_topic"),
                "command_topic": LaunchConfiguration("command_topic"),
                "joint_states_topic": LaunchConfiguration("joint_states_topic"),
                "singular_values_topic": LaunchConfiguration("singular_values_topic"),
                "debug_twist_topic": LaunchConfiguration("debug_twist_topic"),
                "rate_hz": LaunchConfiguration("rate_hz"),
                "command_timeout": LaunchConfiguration("command_timeout"),
                "gamma": LaunchConfiguration("gamma"),
                "singular_gain_position": LaunchConfiguration("singular_gain_position"),
                "singular_gain_angular": LaunchConfiguration("singular_gain_angular"),
                "pinv_tolerance": LaunchConfiguration("pinv_tolerance"),
                "max_joint_velocity": LaunchConfiguration("max_joint_velocity"),
                "max_cartesian_linear_velocity": LaunchConfiguration("max_cartesian_linear_velocity"),
                "max_cartesian_angular_velocity": LaunchConfiguration("max_cartesian_angular_velocity"),
            }
        ],
    )

    return LaunchDescription(declared_arguments + [controller_node])