import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


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

    package_name = 'my_robot_description'
    pkg_share = get_package_share_directory(package_name)
    # Prefer source URDF when available to avoid stale installed files; fallback to installed
    src_urdf = '/home/guenther/ws_restore/src/match_mobile_robotics_jazzy/my_robot_description/urdf/bunker.xacro'
    urdf_file = src_urdf if os.path.exists(src_urdf) else os.path.join(pkg_share, 'urdf', 'bunker.xacro')
    # Prefer source path when developing to avoid stale installed files; fallback to installed
    src_yaml = '/home/guenther/ws_restore/src/match_mobile_robotics_jazzy/my_robot_description/config/controllers_min.yaml'
    # Define the controllers_yaml arg
    controllers_yaml_arg = DeclareLaunchArgument(
        'controllers_yaml',
        default_value=os.path.join(
            get_package_share_directory('my_robot_description'),
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

    # FIX: Ensure Gazebo finds the gz_ros2_control plugin manually
    # We allow the user to execute from workspace root
    gz_ros2_control_lib = '/home/guenther/ws_restore/install/gz_ros2_control/lib'

    print(f"[spawn_with_controllers] Force-setting GZ_SIM_SYSTEM_PLUGIN_PATH to include: {gz_ros2_control_lib}")

    # FIX: Add GZ_SIM_RESOURCE_PATH to allow Gazebo to find meshes in installed packages
    # We add the install/share directories to the resource path
    # Also add the src directory to find franka_description and others if strictly needed 
    
    # Base paths
    ws_root = '/home/guenther/ws_restore'
    install_share = os.path.join(ws_root, 'install', 'share')
    src_dir = os.path.join(ws_root, 'src')
    
    # Existing path
    current_res_path = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    
    # Construct new path
    new_paths = [install_share, src_dir]
    
    # Append existing paths
    if current_res_path:
        new_paths.append(current_res_path)
    
    gz_resource_path = ':'.join(new_paths)
    
    print(f"[spawn_with_controllers] Force-setting GZ_SIM_RESOURCE_PATH to: {gz_resource_path}")

    gz_ros_debug_env = {
        # Make controller initialization failures print their real reason.
        'RCUTILS_LOGGING_SEVERITY_THRESHOLD': 'INFO',
        'RCLCPP_LOG_LEVEL': 'info',
        'GZ_SIM_SYSTEM_PLUGIN_PATH': gz_ros2_control_lib + ':' + os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', ''),
        'GZ_SIM_RESOURCE_PATH': gz_resource_path
    }

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

    # Publisher für /robot_description (für ros_gz_sim create)
    robot_description_pub_root = Node(
        package='my_robot_description',
        executable='robot_description_publisher.py',
        name='robot_description_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}]
    )

    # Removed namespaced publisher; plugin will read /robot_description directly

    # Kein separater ros2_control_node: wir verwenden den Controller-Manager
    # aus dem gz_ros2_control-Plugin (erreichbar unter /controller_manager_node).

    # spawn robot entity in Gazebo after 2s to ensure robot_description published
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
            '--controller-manager', '/controller_manager_node',
            '--param-file', controllers_yaml
        ],
        output='screen'
    )

    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_drive_controller',
            '--controller-manager', '/controller_manager_node',
            '--param-file', controllers_yaml
        ],
        output='screen'
    )

    # Create the launch description
    ld = LaunchDescription()
    
    # Add env vars
    ld.add_action(SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH', 
        value=gz_resource_path
    ))
    ld.add_action(SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value=gz_ros2_control_lib
    ))

    # Add args and nodes
    ld.add_action(controllers_yaml_arg)
    ld.add_action(gz_sim)
    ld.add_action(robot_state_publisher)
    ld.add_action(robot_description_pub_root)
    ld.add_action(ros_gz_bridge)
    ld.add_action(spawn_entity)
    ld.add_action(joint_state_spawner)
    ld.add_action(diff_drive_spawner)

    return ld
