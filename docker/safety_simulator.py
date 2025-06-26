#!/usr/bin/env python3
"""
SDV Safety Application Simulator
Simule les applications critiques de sécurité véhicule
"""

import os
import time
import random
import threading
from datetime import datetime

class SafetyAppSimulator:
    def __init__(self, app_name):
        self.app_name = app_name
        self.running = False
        self.metrics = {
            'start_time': None,
            'cycles': 0,
            'alerts': 0,
            'interventions': 0
        }
        
        # Configuration des applications safety
        self.apps_config = {
            'emergency-brake': {
                'sensors': ['brake_pedal', 'collision_radar', 'speed'],
                'response_time_ms': 10,
                'criticality': 'highest'
            },
            'collision-avoidance': {
                'sensors': ['lidar', 'camera', 'radar'],
                'response_time_ms': 50,
                'criticality': 'highest'
            },
            'lane-keeping': {
                'sensors': ['camera', 'wheel_angle'],
                'response_time_ms': 100,
                'criticality': 'high'
            },
            'driver-monitoring': {
                'sensors': ['interior_camera', 'steering_input'],
                'response_time_ms': 200,
                'criticality': 'highest'
            }
        }
        
        self.config = self.apps_config.get(app_name, {
            'sensors': ['generic_sensor'],
            'response_time_ms': 100,
            'criticality': 'high'
        })
        
    def simulate_sensors(self):
        """Simule les données des capteurs"""
        sensor_data = {}
        for sensor in self.config.get('sensors', []):
            if sensor == 'speed':
                sensor_data[sensor] = random.uniform(0, 130)  # km/h
            elif sensor == 'brake_pedal':
                sensor_data[sensor] = random.uniform(0, 100)  # %
            elif sensor == 'collision_radar':
                sensor_data[sensor] = random.uniform(0.5, 100)  # mètres
            elif sensor == 'steering_input':
                sensor_data[sensor] = random.uniform(-45, 45)  # degrés
            else:
                sensor_data[sensor] = random.uniform(0, 1)  # valeur normalisée
        return sensor_data
    
    def check_safety_conditions(self, sensor_data):
        """Vérifie les conditions de sécurité selon l'application"""
        alerts = []
        
        if self.app_name == 'emergency-brake':
            collision_distance = sensor_data.get('collision_radar', 100)
            speed = sensor_data.get('speed', 0)
            if collision_distance < 2.0 and speed > 30:
                alerts.append('EMERGENCY_BRAKE_REQUIRED')
                
        elif self.app_name == 'collision-avoidance':
            collision_distance = sensor_data.get('collision_radar', 100)
            if collision_distance < 5.0:
                alerts.append('COLLISION_RISK_DETECTED')
                
        elif self.app_name == 'lane-keeping':
            steering = sensor_data.get('steering_input', 0)
            if abs(steering) > 30:
                alerts.append('LANE_DEPARTURE_WARNING')
                
        elif self.app_name == 'driver-monitoring':
            # Simulation de détection d'inattention
            if random.random() < 0.1:  # 10% chance de détection
                alerts.append('DRIVER_ATTENTION_ALERT')
        
        return alerts
    
    def run(self):
        """Boucle principale de simulation"""
        self.running = True
        self.metrics['start_time'] = datetime.now()
        
        print(f"[{datetime.now()}] Starting {self.app_name} safety application")
        print(f"[{datetime.now()}] Criticality: {self.config.get('criticality', 'unknown')}")
        print(f"[{datetime.now()}] Response time: {self.config.get('response_time_ms', 0)}ms")
        
        response_time = self.config.get('response_time_ms', 100) / 1000.0
        
        while self.running:
            cycle_start = time.time()
            
            # Simulation des capteurs
            sensor_data = self.simulate_sensors()
            
            # Vérification conditions de sécurité
            alerts = self.check_safety_conditions(sensor_data)
            
            if alerts:
                self.metrics['alerts'] += 1
                for alert in alerts:
                    print(f"[{datetime.now()}] {self.app_name}: ⚠️  {alert}")
                    # Simulation d'intervention automatique
                    if random.random() < 0.3:  # 30% chance d'intervention
                        self.metrics['interventions'] += 1
                        print(f"[{datetime.now()}] {self.app_name}:  SAFETY_INTERVENTION_ACTIVATED")
            
            # Affichage statut normal périodique
            if self.metrics['cycles'] % 50 == 0:  # Toutes les 50 cycles
                uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
                print(f"[{datetime.now()}] {self.app_name}:  Running normally - "
                      f"Cycle {self.metrics['cycles']}, Uptime: {uptime:.1f}s, "
                      f"Alerts: {self.metrics['alerts']}, Interventions: {self.metrics['interventions']}")
            
            self.metrics['cycles'] += 1
            
            # Respecter le temps de réponse temps réel
            cycle_time = time.time() - cycle_start
            sleep_time = max(0, response_time - cycle_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

if __name__ == '__main__':
    app_name = os.environ.get('APP_NAME', 'emergency-brake')
    
    print(" SDV Safety Application Simulator")
    print("="*50)
    print(f"Application: {app_name}")
    print(f"Priority: {os.environ.get('SDV_PRIORITY', 'critical')}")
    print(f"Real-time mode: {os.environ.get('SDV_REAL_TIME', 'true')}")
    print(f"Pod: {os.environ.get('HOSTNAME', 'unknown')}")
    print("="*50)
    
    simulator = SafetyAppSimulator(app_name)
    
    try:
        simulator.run()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] {app_name} shutting down...")
        uptime = (datetime.now() - simulator.metrics['start_time']).total_seconds()
        print(f"[{datetime.now()}] Final metrics:")
        print(f"  • Uptime: {uptime:.1f}s")
        print(f"  • Cycles: {simulator.metrics['cycles']}")
        print(f"  • Alerts: {simulator.metrics['alerts']}")
        print(f"  • Interventions: {simulator.metrics['interventions']}")
        simulator.running = False 