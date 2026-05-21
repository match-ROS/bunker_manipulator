#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from sensor_msgs.msg import JointState

class HardwareTestSequence(Node):
    def __init__(self):
        super().__init__('hardware_test_sequence')
        
        self.bunker_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.ur_pub = self.create_publisher(JointTrajectory, '/scaled_joint_trajectory_controller/joint_trajectory', 10)
        self.joint_sub = self.create_subscription(JointState, '/joint_states', self.joint_callback, 10)
        
        self.current_angles = {}
        self.start_time = None
        self.current_phase = 0
        
        self.get_logger().info('Warte auf Gelenkdaten vom UR16e...')
        self.control_timer = self.create_timer(0.1, self.control_loop)

    def joint_callback(self, msg):
        if len(msg.name) >= 6:
            self.current_angles = dict(zip(msg.name, msg.position))

    def control_loop(self):
        if not self.current_angles:
            return 
            
        if self.start_time is None:
            self.start_time = self.get_clock().now()
            self.get_logger().info('Starte System-Test-Sequenz!')
            
        elapsed_time = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        msg = Twist()
        
        # --- PHASE 1: 10 cm vorwärts (0 bis 2 Sekunden) ---
        if elapsed_time < 2.0:
            msg.linear.x = 0.05
            msg.angular.z = 0.0
            if self.current_phase != 1:
                self.get_logger().info('Bunker: Fahre 10 cm vorwärts...')
                self.current_phase = 1

        # --- PHASE 2: 10 Grad nach RECHTS drehen (2 bis 3 Sekunden) ---
        elif elapsed_time < 3.0:
            msg.linear.x = 0.0
            msg.angular.z = -0.175 # 0.175 rad = ca. 10 Grad
            if self.current_phase != 2:
                self.get_logger().info('Bunker: Drehe 10 Grad nach rechts...')
                self.current_phase = 2

        # --- PHASE 3: 10 Grad nach LINKS drehen (3 bis 4 Sekunden) ---
        elif elapsed_time < 4.0:
            msg.linear.x = 0.0
            msg.angular.z = 0.175  # Zurück zur Mitte
            if self.current_phase != 3:
                self.get_logger().info('Bunker: Drehe 10 Grad nach links...')
                self.current_phase = 3

        # --- PHASE 4: Bunker stoppen und Arm-Test starten (ab 4 Sekunden) ---
        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            
            if self.current_phase != 4:
                self.get_logger().info('Bunker Test beendet. Starte UR16e Gelenk-Test...')
                self.current_phase = 4
                self.run_arm_test_sequence()
                self.control_timer.cancel()
                
        self.bunker_pub.publish(msg)

    def run_arm_test_sequence(self):
        traj = JointTrajectory()
        traj.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]
        
        base_positions = [
            self.current_angles.get(name, 0.0) for name in traj.joint_names
        ]
        
        time_sec = 0.0 
        
        for i in range(5, -1, -1):
            # Hinweg: +5 Grad (0.087 rad)
            p_out = JointTrajectoryPoint()
            pos_out = list(base_positions) 
            pos_out[i] += 0.087            
            p_out.positions = pos_out
            
            time_sec += 1.5 
            p_out.time_from_start = Duration(sec=int(time_sec), nanosec=int((time_sec % 1) * 1e9))
            traj.points.append(p_out)
            
            # Rückweg: Zurück auf Startposition
            p_back = JointTrajectoryPoint()
            p_back.positions = list(base_positions) 
            
            time_sec += 1.5 
            p_back.time_from_start = Duration(sec=int(time_sec), nanosec=int((time_sec % 1) * 1e9))
            traj.points.append(p_back)

        self.ur_pub.publish(traj)
        
        total_time = time_sec
        self.get_logger().info(f'Gelenk-Test gesendet. Dauer: {total_time} Sekunden.')
        self.get_logger().info('Du kannst das Skript danach mit Strg+C beenden.')

def main(args=None):
    rclpy.init(args=args)
    node = HardwareTestSequence()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Notstopp per Tastatur...')
        node.bunker_pub.publish(Twist()) 
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
