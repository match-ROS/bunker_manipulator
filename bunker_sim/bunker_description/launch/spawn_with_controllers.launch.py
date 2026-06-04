import os
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
    UnsetEnvironmentVariable,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def prepend_env_paths(variable_name, paths):
    existing_paths = os.environ.get(variable_name, '').split(os.pathsep)
    return os.pathsep.join(dict.fromkeys(path for path in [*paths, *existing_paths] if path))


def generate_launch_description():
    # Launch args
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='empty.sdf',
        description='Gazebo world file (e.g. empty.sdf or absolute path)'
    )
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Start Gazebo headless (true/false)'
    )

    package_name = 'bunker_description'
    pkg_share = get_package_share_directory(package_name)
    urdf_file = os.path.join(pkg_share, 'urdf', 'bunkur.xacro')

    # Define the controllers_yaml arg
    controllers_yaml_arg = DeclareLaunchArgument(
        'controllers_yaml',
        default_value=os.path.join(
            get_package_share_directory('bunker_description'),
            'config',
            'test_controllers.yaml'
        ),
        description='Path to the controller configuration file'
    )
    # Use the launch config for xacro command
    controllers_yaml = LaunchConfiguration('controllers_yaml')
    # inject controllers yaml path into xacro so Gazebo plugin can pick it up
    robot_description = ParameterValue(
        Command(['xacro ', urdf_file, ' controllers_yaml:=', controllers_yaml]),
        value_type=str
    )

    print(f"[spawn_with_controllers] Using URDF: {urdf_file}")
    print(f"[spawn_with_controllers] Using controllers YAML: {controllers_yaml}")

    # Gazebo resolves package resources from each sourced colcon prefix's share directory.
    ament_prefixes = os.environ.get('AMENT_PREFIX_PATH', '').split(os.pathsep)
    resource_paths = [os.path.join(prefix, 'share') for prefix in ament_prefixes if prefix]
    resource_paths.insert(0, os.path.dirname(pkg_share))
    gz_resource_path = prepend_env_paths('GZ_SIM_RESOURCE_PATH', resource_paths)

    # Derive the plugin directory from the package index instead of a workspace path.
    gz_ros2_control_lib = os.path.join(get_package_prefix('gz_ros2_control'), 'lib')
    gz_system_plugin_path = prepend_env_paths(
        'GZ_SIM_SYSTEM_PLUGIN_PATH',
        [gz_ros2_control_lib],
    )

    # Launch Gazebo Sim
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}]
    )

    # Kein separater ros2_control_node: wir verwenden den Controller-Manager
    # aus dem gz_ros2_control-Plugin (erreichbar unter /controller_manager).

    # Spawn from the transient-local /robot_description published by robot_state_publisher.
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'bunker', '-x', '0', '-y', '0', '-z', '0.5'],
        output='screen'
    )

    # Bridge node to forward /clock from Gazebo to ROS 2
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # Spawner nodes to load controllers
    joint_state_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager'
        ],
        output='screen'
    )

    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_drive_controller',
            '--controller-manager', '/controller_manager'
        ],
        output='screen'
    )

    ur_joint_trajectory_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'ur_joint_trajectory_controller',
            '--controller-manager', '/controller_manager'
        ],
        output='screen'
    )

    inactive_ur_controllers_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'ur_scaled_joint_trajectory_controller',
            'ur_forward_velocity_controller',
            'ur_forward_position_controller',
            '--controller-manager', '/controller_manager',
            '--inactive'
        ],
        output='screen'
    )

    spawn_joint_state_after_robot = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            # The Gazebo plugin creates /controller_manager asynchronously after insertion.
            on_exit=[TimerAction(period=3.0, actions=[joint_state_spawner])],
        )
    )

    spawn_controllers_after_joint_state = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_spawner,
            on_exit=[
                diff_drive_spawner,
                ur_joint_trajectory_spawner,
                inactive_ur_controllers_spawner,
            ],
        )
    )

    # Create the launch description
    ld = LaunchDescription()

    # Snap-packaged IDEs export GTK/plugin paths from their runtime. Native Gazebo must not load
    # those libraries because they are built against a different glibc.
    for variable_name in (
        'GTK_PATH',
        'GIO_EXTRA_MODULES',
        'QT_PLUGIN_PATH',
        'QT_QPA_PLATFORM_PLUGIN_PATH',
        'SNAP',
        'SNAP_NAME',
        'SNAP_REVISION',
        'SNAP_VERSION',
    ):
        ld.add_action(UnsetEnvironmentVariable(variable_name))

    # Add env vars
    ld.add_action(SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_resource_path
    ))
    ld.add_action(SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value=gz_system_plugin_path
    ))

    # Add args and nodes
    ld.add_action(controllers_yaml_arg)
    ld.add_action(gz_sim)
    ld.add_action(robot_state_publisher)
    ld.add_action(ros_gz_bridge)
    ld.add_action(spawn_entity)
    ld.add_action(spawn_joint_state_after_robot)
    ld.add_action(spawn_controllers_after_joint_state)

    return ld
