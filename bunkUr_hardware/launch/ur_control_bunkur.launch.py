from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import (
    AndSubstitution,
    LaunchConfiguration,
    NotSubstitution,
    PathJoinSubstitution,
)
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterFile
from launch_ros.substitutions import FindPackageShare


def launch_setup(context):
    ur_type = LaunchConfiguration("ur_type")
    robot_ip = LaunchConfiguration("robot_ip")
    controllers_file = LaunchConfiguration("controllers_file")
    description_launchfile = LaunchConfiguration("description_launchfile")
    use_mock_hardware = LaunchConfiguration("use_mock_hardware")
    controller_spawner_timeout = LaunchConfiguration("controller_spawner_timeout")
    initial_joint_controller = LaunchConfiguration("initial_joint_controller")
    activate_joint_controller = LaunchConfiguration("activate_joint_controller")
    start_forward_velocity_controller = LaunchConfiguration(
        "start_forward_velocity_controller"
    )
    launch_rviz = LaunchConfiguration("launch_rviz")
    rviz_config_file = LaunchConfiguration("rviz_config_file")
    headless_mode = LaunchConfiguration("headless_mode")
    launch_dashboard_client = LaunchConfiguration("launch_dashboard_client")
    use_tool_communication = LaunchConfiguration("use_tool_communication")
    tool_device_name = LaunchConfiguration("tool_device_name")
    tool_tcp_port = LaunchConfiguration("tool_tcp_port")
    controller_manager = LaunchConfiguration("controller_manager")
    namespace = LaunchConfiguration("namespace")

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        namespace=namespace,
        parameters=[
            LaunchConfiguration("update_rate_config_file"),
            ParameterFile(controllers_file, allow_substs=True),
        ],
        output="screen",
    )

    dashboard_client_node = IncludeLaunchDescription(
        condition=IfCondition(
            AndSubstitution(launch_dashboard_client, NotSubstitution(use_mock_hardware))
        ),
        launch_description_source=AnyLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ur_robot_driver"), "launch", "ur_dashboard_client.launch.py"]
            )
        ),
        launch_arguments={
            "robot_ip": robot_ip,
        }.items(),
    )

    robot_state_helper_node = Node(
        package="ur_robot_driver",
        executable="robot_state_helper",
        name="ur_robot_state_helper",
        namespace=namespace,
        output="screen",
        condition=UnlessCondition(use_mock_hardware),
        parameters=[
            {"headless_mode": headless_mode},
            {"robot_ip": robot_ip},
        ],
    )

    tool_communication_node = Node(
        package="ur_robot_driver",
        condition=IfCondition(use_tool_communication),
        executable="tool_communication.py",
        name="ur_tool_comm",
        namespace=namespace,
        output="screen",
        parameters=[
            {
                "robot_ip": robot_ip,
                "tcp_port": tool_tcp_port,
                "device_name": tool_device_name,
            }
        ],
    )

    urscript_interface = Node(
        package="ur_robot_driver",
        executable="urscript_interface",
        namespace=namespace,
        parameters=[{"robot_ip": robot_ip}],
        output="screen",
        condition=UnlessCondition(use_mock_hardware),
    )

    controller_stopper_node = Node(
        package="ur_robot_driver",
        executable="controller_stopper_node",
        name="controller_stopper",
        namespace=namespace,
        output="screen",
        emulate_tty=True,
        condition=UnlessCondition(use_mock_hardware),
        parameters=[
            {"headless_mode": headless_mode},
            {"joint_controller_active": activate_joint_controller},
            {
                "consistent_controllers": [
                    "io_and_status_controller",
                    "joint_state_broadcaster",
                    "speed_scaling_state_broadcaster",
                    "tcp_pose_broadcaster",
                    "ur_configuration_controller",
                ]
            },
        ],
    )

    rviz_node = Node(
        package="rviz2",
        condition=IfCondition(launch_rviz),
        executable="rviz2",
        name="rviz2",
        namespace=namespace,
        output="log",
        arguments=["-d", rviz_config_file],
    )

    trajectory_until_node = Node(
        package="ur_robot_driver",
        executable="trajectory_until_node",
        name="trajectory_until_node",
        namespace=namespace,
        output="screen",
        parameters=[
            {
                "motion_controller": initial_joint_controller,
            },
        ],
    )

    def controller_spawner(controllers, active=True):
        inactive_flags = ["--inactive"] if not active else []
        return Node(
            package="controller_manager",
            executable="spawner",
            namespace=namespace,
            arguments=[
                "--controller-manager",
                controller_manager,
                "--controller-manager-timeout",
                controller_spawner_timeout,
            ]
            + inactive_flags
            + controllers,
            output="screen",
        )

    controllers_active = [
        "joint_state_broadcaster",
        "io_and_status_controller",
        "speed_scaling_state_broadcaster",
        "tcp_pose_broadcaster",
        "ur_configuration_controller",
    ]
    controllers_inactive = [
        "scaled_joint_trajectory_controller",
        "joint_trajectory_controller",
        "forward_velocity_controller",
        "forward_position_controller",
        "forward_effort_controller",
        "force_mode_controller",
        "passthrough_trajectory_controller",
        "freedrive_mode_controller",
        "tool_contact_controller",
    ]
    if activate_joint_controller.perform(context) == "true":
        controllers_active.append(initial_joint_controller.perform(context))
        controllers_inactive.remove(initial_joint_controller.perform(context))

    if start_forward_velocity_controller.perform(context) == "true":
        if "forward_velocity_controller" in controllers_inactive:
            controllers_inactive.remove("forward_velocity_controller")
        if "forward_velocity_controller" not in controllers_active:
            controllers_active.append("forward_velocity_controller")

    if use_mock_hardware.perform(context) == "true":
        controllers_active.remove("tcp_pose_broadcaster")

    controller_spawners = [
        controller_spawner(controllers_active),
        controller_spawner(controllers_inactive, active=False),
    ]

    rsp = GroupAction(
        actions=[
            PushRosNamespace(namespace),
            IncludeLaunchDescription(
                AnyLaunchDescriptionSource(description_launchfile),
                launch_arguments={
                    "robot_ip": robot_ip,
                    "ur_type": ur_type,
                }.items(),
            ),
        ]
    )

    nodes_to_start = [
        control_node,
        dashboard_client_node,
        robot_state_helper_node,
        tool_communication_node,
        controller_stopper_node,
        urscript_interface,
        rsp,
        rviz_node,
        trajectory_until_node,
    ] + controller_spawners

    return nodes_to_start


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "namespace",
            default_value="/bunkur/ur",
            description="Namespace for the UR driver and controller manager.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument("ur_type", default_value="ur16e")
    )
    declared_arguments.append(
        DeclareLaunchArgument("robot_ip", default_value="192.168.1.102")
    )
    declared_arguments.append(
        DeclareLaunchArgument("launch_rviz", default_value="false")
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "controllers_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("bunkUr_hardware"), "config", "ur_controllers_bunkur.yaml"]
            ),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_launchfile",
            default_value=PathJoinSubstitution(
                [FindPackageShare("ur_robot_driver"), "launch", "ur_rsp.launch.py"]
            ),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument("tf_prefix", default_value="")
    )
    declared_arguments.append(
        DeclareLaunchArgument("use_mock_hardware", default_value="false")
    )
    declared_arguments.append(
        DeclareLaunchArgument("mock_sensor_commands", default_value="false")
    )
    declared_arguments.append(
        DeclareLaunchArgument("headless_mode", default_value="false")
    )
    declared_arguments.append(
        DeclareLaunchArgument("launch_dashboard_client", default_value="true")
    )
    declared_arguments.append(
        DeclareLaunchArgument("use_tool_communication", default_value="false")
    )
    declared_arguments.append(
        DeclareLaunchArgument("tool_device_name", default_value="/tmp/ttyUR")
    )
    declared_arguments.append(
        DeclareLaunchArgument("tool_tcp_port", default_value="54321")
    )
    declared_arguments.append(
        DeclareLaunchArgument("controller_spawner_timeout", default_value="10")
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "initial_joint_controller",
            default_value="scaled_joint_trajectory_controller",
            choices=[
                "scaled_joint_trajectory_controller",
                "joint_trajectory_controller",
                "forward_velocity_controller",
                "forward_position_controller",
                "freedrive_mode_controller",
                "passthrough_trajectory_controller",
            ],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument("activate_joint_controller", default_value="true")
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "start_forward_velocity_controller",
            default_value="true",
            description="Auto-configure and activate forward_velocity_controller on startup.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "rviz_config_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("ur_robot_driver"), "rviz", "view_robot.rviz"]
            ),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "controller_manager",
            default_value=PathJoinSubstitution(
                [LaunchConfiguration("namespace"), "controller_manager"]
            ),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            name="update_rate_config_file",
            default_value=[
                PathJoinSubstitution(
                    [FindPackageShare("ur_robot_driver"), "config"]
                ),
                "/",
                LaunchConfiguration("ur_type"),
                "_update_rate.yaml",
            ],
        )
    )

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
