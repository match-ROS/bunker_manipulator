import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue  # <--- NEU: Dieser Import hat gefehlt

def generate_launch_description():
    
    # *** HIER BITTE DEINEN DATEINAMEN PRÜFEN ***
    # Schau in deinen urdf Ordner, wie die Datei heißt (z.B. mur620.urdf.xacro oder my_robot.urdf)
    urdf_file_name = 'bunker.xacro'

    pkg_share = get_package_share_directory('my_robot_description')
    urdf_path = os.path.join(pkg_share, 'urdf', urdf_file_name)
    
    # Pfad zur Controller-Konfigurationsdatei
    controllers_yaml_path = os.path.join(pkg_share, 'config', 'controllers_min.yaml')

    # Wir wickeln den Command in ParameterValue ein, damit ROS nicht meckert
    # WICHTIG: Wir übergeben jetzt den Pfad als Argument an xacro!
    robot_description_content = ParameterValue(
        Command(['xacro ', urdf_path, ' controllers_yaml:=', controllers_yaml_path]),
        value_type=str
    )

    # 2. Robot State Publisher starten
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content}]
    )

    # 3. Der eigentliche Spawn-Befehl für Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'my_custom_robot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.5'
        ],
        output='screen'
    )

    # 4. Controller Spawner (NEU)
    # Wir starten die Spawner direkt hier, damit du es nicht manuell machen musst.
    # WICHTIG: Wir setzen use_sim_time=True, damit sie synchron mit Gazebo laufen.
    
    # joint_state_broadcaster_spawner = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager", "--param-file", controllers_yaml_path],
    # )

    # diff_drive_controller_spawner = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["diff_drive_controller", "--controller-manager", "/controller_manager", "--param-file", controllers_yaml_path],
    # )

    return LaunchDescription([
        robot_state_publisher,
        spawn_entity,
        # joint_state_broadcaster_spawner,
        # diff_drive_controller_spawner
    ])
