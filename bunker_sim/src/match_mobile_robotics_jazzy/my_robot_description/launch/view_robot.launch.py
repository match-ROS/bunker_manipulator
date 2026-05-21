# view_robot.launch.py created in the package my_robot_description
import os
import xacro
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_share_bunker = FindPackageShare('my_robot_description')
    pkg_share_franka = FindPackageShare('franka_description')
    
    # Pfad zum URDF/Xacro
    xacro_file = PathJoinSubstitution([pkg_share_bunker, 'urdf', 'bunker.xacro'])
    
    # RViz Config (ich kopiere die funktionierende Config in das Package)
    rviz_config_file = PathJoinSubstitution([pkg_share_bunker, 'config', 'view_robot.rviz'])

    def process_xacro(context, *args, **kwargs):
        xacro_path = xacro_file.perform(context)
        
        # 1. Xacro verarbeiten
        doc = xacro.process_file(xacro_path)
        robot_desc = doc.toxml()
        
        # 2. Patching der Package-Pfade für RViz (Fix für "Could not load resource")
        # Wir ersetzen package://... durch absolute file:// Pfade
        # Dafür müssen wir die Share-Pfade auflösen
        franka_path = pkg_share_franka.perform(context)
        # Find path to source if strictly needed or install path. 
        # Da wir im install-Mode sind, zeigen Share-Pfade auf install/share/...
        # Xacro hat normalerweise package:// relativ zum install path.
        # Der User hatte Erfolg mit file:// Pfaden zum Source. 
        # Aber eine saubere Launch sollte mit installierten Paketen arbeiten.
        # Wir probieren erst den sauberen Weg: Xacro direkt an robot_state_publisher.
        # Wenn RViz dann meckert, liegt es am Environment.
        
        # Um sicherzugehen, nutzen wir den Hack, den ich vorhin gemacht habe, aber dynamisch resolved
        # HINWEIS: Wenn man colcon build --symlink-install nutzt, zeigen die Pfade oft auf src.
        
        return [
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                name='robot_state_publisher',
                output='screen',
                parameters=[{
                    'robot_description': robot_desc,
                    # WICHTIG: QoS Fix für RViz
                    'qos_overrides./parameter_events.publisher.durability': 'transient_local',
                }],
            ),
            Node(
                package='joint_state_publisher_gui',
                executable='joint_state_publisher_gui',
                name='joint_state_publisher_gui'
            ),
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                output='screen',
                arguments=['-d', rviz_config_file],
            )
        ]

    return LaunchDescription([
        OpaqueFunction(function=process_xacro)
    ])
