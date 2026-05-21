# Bunker_UR16e: Bunker Pro 2.0, UR16e & Dual-LiDAR System

Dieses Repository enthält die Konfiguration und Installationsskripte für die Kombination aus einer AgileX Bunker Pro 2.0 Basis, einem Universal Robots UR16e Arm und einem Dual-LiDAR Setup (2x RoboSense Airy) unter ROS 2 Jazzy (Ubuntu 24.04).

---

## 📋 Voraussetzungen

* **OS:** Ubuntu 24.04 LTS
* **ROS 2:** Jazzy Jalisco (Desktop-Full empfohlen)

**Benötigte Hardware:**
* CAN-USB Adapter (für Bunker)
* Gigabit-Netzwerk-Switch (Zwingend für Dual-LiDAR Datenraten)
* 12V Step-Down Converter (Stromversorgung LiDARs)
* 300W 20A Step-Down Converter (auf 19V eingestellt für den PC)

---

## 🛠️ Installation

### 1. System-Treiber (UR16e)
Der UR-Treiber wird stabil über die offiziellen Paketquellen installiert, um Versionskonflikte beim Kompilieren zu vermeiden.

```bash
sudo apt update
sudo apt install ros-jazzy-ur-robot-driver ros-jazzy-ur-moveit-config ros-jazzy-teleop-twist-keyboard -y
```

### 2. Workspace & Automatisches Setup (Bunker)
Nutze das vorbereitete Setup-Skript, anstatt alles manuell zu machen. Es erstellt den Workspace, klont die AgileX-Repos und fixt die fehlerhafte Motor-Schleife im SDK automatisch.

```bash
# In dein Projekt-Verzeichnis gehen
cd ~/Bunker_UR16e

# Skript ausführbar machen und starten
chmod +x scripts/setup_workspace.sh
./scripts/setup_workspace.sh
```

### 3. RoboSense LiDAR Treiber (rslidar_sdk)
Für die LiDARs benötigen wir das offizielle SDK sowie das zugehörige Message-Paket.

```bash
cd ~/bunker_ur16e_ws/src
git clone --recursive [https://github.com/RoboSense-LiDAR/rslidar_sdk.git](https://github.com/RoboSense-LiDAR/rslidar_sdk.git)
git clone [https://github.com/RoboSense-LiDAR/rslidar_msg.git](https://github.com/RoboSense-LiDAR/rslidar_msg.git)
```

**Wichtig (ROS 2 Anpassung):** Öffne die `CMakeLists.txt` im Ordner `rslidar_sdk` und ändere die Zeile `set(COMPILE_ROS_VERSION "1")` zwingend zu **`"2"`**.

Kompiliere danach den Workspace:

```bash
cd ~/bunker_ur16e_ws
colcon build --symlink-install
source install/setup.bash
```

---

## ⚙️ Hardware-Setup & Netzwerk

### Netzwerk (Allgemein)
* **PC IP:** `192.168.1.101` (Netzmaske: 255.255.255.0, Gateway leer lassen!)
* **UR16e IP:** `192.168.1.102`
* **Firewall:** Muss für den UDP-Datenstrom der LiDARs zwingend deaktiviert sein!
  ```bash
  sudo ufw disable
  ```

### CAN-Bus (Bunker)
Der CAN-USB Adapter muss vor dem Start aktiviert werden:
```bash
sudo modprobe gs_usb
sudo ip link set can0 up type can bitrate 500000
```

### Netzwerk (Dual-LiDAR Setup)
Da beide Sensoren ab Werk dieselbe IP (`192.168.1.200`) haben, müssen sie nacheinander **einzeln** über das Web-Interface im Browser konfiguriert werden:
* **LiDAR 1 (Vorne):** Device IP: `192.168.1.201` | Dest. IP: `192.168.1.101` | MSOP: `6699` | DIFOP: `7788`
* **LiDAR 2 (Hinten):** Device IP: `192.168.1.202` | Dest. IP: `192.168.1.101` | MSOP: `6700` | DIFOP: `7789`

---

## 🔧 Konfiguration des LiDAR-SDKs

Die Konfiguration des Dual-Setups erfordert Anpassungen in zwei Dateien im Ordner `src/rslidar_sdk/`:

### 1. `config/config.yaml` (Sensoren definieren)
Wir nutzen einen duplizierten `driver`-Block, um beide Sensoren gleichzeitig abzufragen, und trennen die ROS-Topics (`_front` und `_back`):

```yaml
common:
  msg_source: 1                                         
  send_packet_ros: false                                
  send_point_cloud_ros: true                            
lidar:
  # ================= SENSOR 1 (VORNE) =================
  - driver:
      lidar_type: RSAIRY             
      msop_port: 6699              
      difop_port: 7788             
      imu_port: 0                  
      min_distance: 0.2            
      max_distance: 60               
      use_lidar_clock: true        
    ros:
      ros_frame_id: rslidar_front          
      ros_recv_packet_topic: /rslidar_packets_front          
      ros_send_packet_topic: /rslidar_packets_front          
      ros_send_imu_data_topic: /rslidar_imu_data_front         
      ros_send_point_cloud_topic: /rslidar_points_front      
      ros_queue_length: 100   

  # ================= SENSOR 2 (HINTEN) =================
  - driver:
      lidar_type: RSAIRY             
      msop_port: 6700               
      difop_port: 7789              
      imu_port: 0                  
      min_distance: 0.2            
      max_distance: 60               
      use_lidar_clock: true        
    ros:
      ros_frame_id: rslidar_back          
      ros_recv_packet_topic: /rslidar_packets_back          
      ros_send_packet_topic: /rslidar_packets_back          
      ros_send_imu_data_topic: /rslidar_imu_data_back         
      ros_send_point_cloud_topic: /rslidar_points_back      
      ros_queue_length: 100                             
```

### 2. `launch/start.py` (TF-Baum für RViz)
Damit RViz beide Sensoren räumlich zuordnen kann, publizieren wir statische Transforms (TF) vom Roboter-Zentrum (`base_link`) zu den Sensoren (`rslidar_front` & `rslidar_back`):
*(Hinweis: Positionen in X/Y/Z müssen am echten Roboter nachgemessen und hier angepasst werden).*

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    rviz_config = os.path.join(get_package_share_directory('rslidar_sdk'), 'rviz', 'rviz2.rviz')
    return LaunchDescription([
        Node(namespace='rslidar_sdk', package='rslidar_sdk', executable='rslidar_sdk_node', output='screen', parameters=[{'config_path': ''}]),
        Node(package='tf2_ros', executable='static_transform_publisher', name='tf_front', arguments=['0.5', '0.0', '0.5', '0', '0', '0', 'base_link', 'rslidar_front']),
        Node(package='tf2_ros', executable='static_transform_publisher', name='tf_back', arguments=['-0.5', '0.0', '0.5', '3.14159', '0', '0', 'base_link', 'rslidar_back']),
        Node(namespace='rviz2', package='rviz2', executable='rviz2', arguments=['-d', rviz_config])
    ])
```

---

## 🚀 Betrieb (Startsequenz)

Bitte halte dich an diese Startreihenfolge (jeweils in einem eigenen Terminal ausführen):

**Schritt 1: UR16e Treiber**
*(Zuerst am UR-Tablet das Programm "External Control" starten!)*
```bash
source /opt/ros/jazzy/setup.bash
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur16e robot_ip:=192.168.1.102 launch_rviz:=false
```

**Schritt 2: Bunker Base**
```bash
source ~/bunker_ur16e_ws/install/setup.bash
ros2 launch bunker_base bunker_base.launch.py
```

**Schritt 3: Dual-LiDAR Starten (inkl. RViz)**
```bash
source ~/bunker_ur16e_ws/install/setup.bash
ros2 launch rslidar_sdk start.py
```
*(Wichtig: In RViz als "Fixed Frame" zwingend `base_link` eintragen und die Topics `/rslidar_points_front` sowie `/rslidar_points_back` manuell hinzufügen).*

**Schritt 4: Steuerung**
* **Fahren (Tastatur):** `ros2 run teleop_twist_keyboard teleop_twist_keyboard`
* **Arm (MoveIt):** `ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur16e robot_ip:=192.168.1.102 launch_rviz:=true`

---

## 💻 Eigene Programme schreiben (API)

Wenn du eigene ROS 2 Nodes schreibst, sind das die wichtigsten Schnittstellen deines Roboters:

### 1. Bunker Base (Fahren)
* **Topic:** `/cmd_vel`
* **Typ:** `geometry_msgs/msg/Twist`
* **Steuerung:** `linear.x` (Vorwärts/Rückwärts in m/s), `angular.z` (Drehung in rad/s).

### 2. UR16e Arm (Bewegen)
* **Topic:** `/scaled_joint_trajectory_controller/joint_trajectory`
* **Typ:** `trajectory_msgs/msg/JointTrajectory`
* **Gelenkreihenfolge:** `shoulder_pan_joint`, `shoulder_lift_joint`, `elbow_joint`, `wrist_1_joint`, `wrist_2_joint`, `wrist_3_joint`.

### 3. Dual-LiDAR (Wahrnehmung)
* **Topic Vorne:** `/rslidar_points_front`
* **Topic Hinten:** `/rslidar_points_back`
* **Typ:** `sensor_msgs/msg/PointCloud2`
* **Einsatz:** Liefert dichte 3D-Punktwolken (RSAIRY: bis 60m). Ideal für SLAM (Kartierung) und Hinderniserkennung.

### 4. Sensorik (Zustände)
* **Topic:** `/joint_states`
* **Typ:** `sensor_msgs/msg/JointState`
* **Einsatz:** Liefert ca. 100x pro Sekunde die exakten Positionen aller Räder und Arm-Gelenke.
