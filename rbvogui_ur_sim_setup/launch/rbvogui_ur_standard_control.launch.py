from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    robot_id = LaunchConfiguration('robot_id')
    use_sim_time = LaunchConfiguration('use_sim_time')
    controller_config = PathJoinSubstitution([
        FindPackageShare('rbvogui_ur_sim_setup'),
        'config',
        'rbvogui_standard_controllers.yaml',
    ])

    world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('robotnik_gazebo_ignition'),
            'launch',
            'spawn_world.launch.py',
        ])),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'gui': LaunchConfiguration('gui'),
        }.items(),
    )

    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('robotnik_description'),
            'launch',
            'robot_description.launch.py',
        ])),
        launch_arguments={
            'verbose': 'false',
            'robot_xacro_path': PathJoinSubstitution([
                FindPackageShare('rbvogui_ur_sim_setup'),
                'urdf',
                'rbvogui_ur_standard_control.urdf.xacro',
            ]),
            'frame_prefix': [robot_id, '_'],
            'namespace': robot_id,
            'gazebo_ignition': 'true',
            'arm_type': LaunchConfiguration('arm_type'),
            'low_performance_simulation': 'true',
        }.items(),
    )

    create_robot = Node(
        package='ros_gz_sim',
        executable='create',
        namespace=robot_id,
        arguments=[
            '-name', robot_id,
            '-topic', 'robot_description',
            '-robot_namespace', robot_id,
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
        ],
        output='screen',
    )

    model_pose_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            [
                '/world/robotnik_simple/dynamic_pose/info'
                '@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            ],
        ],
        output='screen',
    )

    robot_pose_publisher = Node(
        package='rbvogui_ur_sim_setup',
        executable='tf_model_pose_to_pose_stamped.py',
        name='rbvogui_robot_pose_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'input_topic': '/world/robotnik_simple/dynamic_pose/info',
            'output_topic': '/robot_pose',
            'model_frame': robot_id,
            'world_frame': 'robotnik_simple',
            'fallback_transform_index': 0,
            'publish_tf': True,
            'tf_child_frame': [robot_id, '_base_footprint'],
        }],
    )

    tcp_pose_publisher = Node(
        package='ur_trajectory_follower',
        executable='current_pose_from_tf',
        name='rbvogui_current_tcp_pose_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'target_frame': 'robotnik_simple',
            'source_frame': [robot_id, '_arm_tool0'],
            'pose_topic': '/current_tcp_pose',
            'publish_rate': 20.0,
        }],
    )

    controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        namespace=robot_id,
        arguments=[
            '--controller-manager-timeout', '60',
            '--service-call-timeout', '60',
            '--param-file', controller_config,
            'joint_state_broadcaster',
            'steering_position_controller',
            'wheel_velocity_controller',
            'joint_trajectory_controller',
        ],
        output='screen',
    )

    swerve_controller = Node(
        package='rbvogui_ur_sim_setup',
        executable='rbvogui_swerve_controller.py',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'cmd_vel_topic': [
                '/', robot_id, '/robotnik_base_control/cmd_vel_unstamped'
            ],
            'steering_command_topic': [
                '/', robot_id, '/steering_position_controller/commands'
            ],
            'wheel_command_topic': [
                '/', robot_id, '/wheel_velocity_controller/commands'
            ],
            'joint_states_topic': ['/', robot_id, '/joint_states'],
            'joint_prefix': [robot_id, '_'],
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument('robot_id', default_value='robot'),
        DeclareLaunchArgument('arm_type', default_value='ur5e'),
        DeclareLaunchArgument('world', default_value='empty'),
        DeclareLaunchArgument('gui', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.1'),
        world,
        robot_description,
        TimerAction(period=2.0, actions=[create_robot]),
        TimerAction(period=3.0, actions=[model_pose_bridge]),
        TimerAction(period=3.5, actions=[robot_pose_publisher]),
        TimerAction(period=4.0, actions=[controller_spawner]),
        TimerAction(period=7.0, actions=[tcp_pose_publisher]),
        TimerAction(period=8.0, actions=[swerve_controller]),
    ])
