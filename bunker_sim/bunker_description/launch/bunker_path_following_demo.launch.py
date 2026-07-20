from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _optional_sim_launch(context, *args, **kwargs):
    if LaunchConfiguration('launch_sim').perform(context).strip().lower() not in {'1', 'true', 'yes', 'on'}:
        return []

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bunker_description'),
                    'launch',
                    'spawn_with_controllers.launch.py',
                ])
            ),
            launch_arguments={
                'launch_rviz': LaunchConfiguration('launch_rviz'),
                'headless': LaunchConfiguration('headless'),
                'ur_type': 'ur20',
            }.items(),
        )
    ]


def generate_launch_description():
    default_config = PathJoinSubstitution([
        FindPackageShare('bunker_description'),
        'config',
        'bunker_simple_base_follower.yaml',
    ])

    path_generator = Node(
        package='parse_paths',
        executable='test_path_generator',
        name='test_path_generator',
        output='screen',
        parameters=[
            LaunchConfiguration('config_file'),
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'frame_id': LaunchConfiguration('path_frame'),
                'path_topic': LaunchConfiguration('path_topic'),
                'path_type': LaunchConfiguration('path_type'),
            },
        ],
    )

    base_follower = Node(
        package='base_trajectory_follower',
        executable='simple_base_follower',
        name='simple_base_follower',
        output='screen',
        parameters=[
            LaunchConfiguration('config_file'),
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'path_topic': LaunchConfiguration('path_topic'),
                'robot_pose_topic': LaunchConfiguration('robot_pose_topic'),
                'cmd_vel_topic': LaunchConfiguration('cmd_vel_topic'),
                'output_stamped': LaunchConfiguration('output_stamped'),
            },
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('config_file', default_value=default_config),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('launch_sim', default_value='false'),
        DeclareLaunchArgument('launch_rviz', default_value='false'),
        DeclareLaunchArgument('headless', default_value='true'),
        DeclareLaunchArgument('path_type', default_value='line'),
        DeclareLaunchArgument('path_frame', default_value='map'),
        DeclareLaunchArgument('path_topic', default_value='/bunker_base_path'),
        DeclareLaunchArgument('robot_pose_topic', default_value='/robot_pose'),
        DeclareLaunchArgument('cmd_vel_topic', default_value='/diff_drive_controller/cmd_vel'),
        DeclareLaunchArgument('output_stamped', default_value='true'),
        OpaqueFunction(function=_optional_sim_launch),
        path_generator,
        base_follower,
    ])
