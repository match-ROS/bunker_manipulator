from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument('sim', default_value='false'),
        DeclareLaunchArgument('robot_name', default_value='bunkur'),
        DeclareLaunchArgument('arm', default_value='ur'),
        DeclareLaunchArgument('base_link', default_value='base_link'),
        DeclareLaunchArgument('tip_link', default_value='tool0'),
        DeclareLaunchArgument('fixed_tool_offset_xyz', default_value='[0.0, 0.0, 0.0]'),
        DeclareLaunchArgument(
            'fixed_tool_offset_quaternion_xyzw',
            default_value='[0.0, 0.0, 0.0, 1.0]',
        ),
        DeclareLaunchArgument('spray_distance_topic', default_value='/spray_distance_smoothed'),
        DeclareLaunchArgument('robot_description_topic', default_value='/robot_description'),
        DeclareLaunchArgument('twist_topic', default_value='~/twist_cmd'),
        DeclareLaunchArgument(
            'command_topic',
            default_value='/forward_velocity_controller/commands',
        ),
        DeclareLaunchArgument('joint_states_topic', default_value='/joint_states'),
        DeclareLaunchArgument(
            'singular_values_topic',
            default_value='/jparse_velocity_controller_ur/singular_values',
        ),
        DeclareLaunchArgument(
            'debug_twist_topic',
            default_value='/jparse_velocity_controller_ur/debug_twist',
        ),
        DeclareLaunchArgument(
            'readiness_topic',
            default_value='/jparse_velocity_controller_ur/ready',
        ),
        DeclareLaunchArgument('rate_hz', default_value='500.0'),
        DeclareLaunchArgument('command_timeout', default_value='0.12'),
        DeclareLaunchArgument('joint_state_timeout', default_value='0.5'),
        DeclareLaunchArgument('command_joint_names_csv', default_value=''),
        DeclareLaunchArgument('gamma', default_value='0.1'),
        DeclareLaunchArgument('singular_gain_position', default_value='1.0'),
        DeclareLaunchArgument('singular_gain_angular', default_value='1.0'),
        DeclareLaunchArgument('pinv_tolerance', default_value='1.0e-6'),
        DeclareLaunchArgument('max_joint_velocity', default_value='1.5'),
        DeclareLaunchArgument('max_cartesian_linear_velocity', default_value='0.25'),
        DeclareLaunchArgument('max_cartesian_angular_velocity', default_value='0.8'),
    ]

    controller_node = Node(
        package='controllers_ros2',
        executable='jparse_velocity_controller',
        output='screen',
        parameters=[
            {
                'use_sim_time': ParameterValue(LaunchConfiguration('sim'), value_type=bool),
                'robot_name': LaunchConfiguration('robot_name'),
                'arm': LaunchConfiguration('arm'),
                'base_link': LaunchConfiguration('base_link'),
                'tip_link': LaunchConfiguration('tip_link'),
                'fixed_tool_offset_xyz': LaunchConfiguration('fixed_tool_offset_xyz'),
                'fixed_tool_offset_quaternion_xyzw': LaunchConfiguration(
                    'fixed_tool_offset_quaternion_xyzw'
                ),
                'spray_distance_topic': LaunchConfiguration('spray_distance_topic'),
                'robot_description_topic': LaunchConfiguration('robot_description_topic'),
                'twist_topic': LaunchConfiguration('twist_topic'),
                'command_topic': LaunchConfiguration('command_topic'),
                'joint_states_topic': LaunchConfiguration('joint_states_topic'),
                'singular_values_topic': LaunchConfiguration('singular_values_topic'),
                'debug_twist_topic': LaunchConfiguration('debug_twist_topic'),
                'readiness_topic': LaunchConfiguration('readiness_topic'),
                'rate_hz': LaunchConfiguration('rate_hz'),
                'command_timeout': LaunchConfiguration('command_timeout'),
                'joint_state_timeout': LaunchConfiguration('joint_state_timeout'),
                'command_joint_names_csv': LaunchConfiguration('command_joint_names_csv'),
                'gamma': LaunchConfiguration('gamma'),
                'singular_gain_position': LaunchConfiguration('singular_gain_position'),
                'singular_gain_angular': LaunchConfiguration('singular_gain_angular'),
                'pinv_tolerance': LaunchConfiguration('pinv_tolerance'),
                'max_joint_velocity': LaunchConfiguration('max_joint_velocity'),
                'max_cartesian_linear_velocity': LaunchConfiguration(
                    'max_cartesian_linear_velocity'
                ),
                'max_cartesian_angular_velocity': LaunchConfiguration(
                    'max_cartesian_angular_velocity'
                ),
            }
        ],
    )

    return LaunchDescription(declared_arguments + [controller_node])
