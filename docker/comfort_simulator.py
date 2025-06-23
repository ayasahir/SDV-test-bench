#!/usr/bin/env python3
"""
SDV Comfort Application Simulator
Simule les applications de confort et commodité véhicule
"""

import os
import time
import random
import threading
from datetime import datetime

class ComfortAppSimulator:
    def __init__(self, app_name):
        self.app_name = app_name
        self.running = False
        self.metrics = {
            'start_time': None,
            'cycles': 0,
            'adjustments': 0,
            'user_requests': 0
        }
        
        # Configuration des applications comfort
        self.apps_config = {
            'climate-control': {
                'sensors': ['interior_temp', 'exterior_temp', 'humidity'],
                'actuators': ['hvac_system', 'fan_speed'],
                'update_interval_ms': 2000,
                'priority': 'medium'
            },
            'seat-adjustment': {
                'sensors': ['seat_position', 'user_preference'],
                'actuators': ['seat_motor'],
                'update_interval_ms': 5000,
                'priority': 'low'
            },
            'lighting-control': {
                'sensors': ['ambient_light', 'time_of_day'],
                'actuators': ['interior_lights', 'dashboard_lights'],
                'update_interval_ms': 3000,
                'priority': 'medium'
            },
            'parking-assist': {
                'sensors': ['ultrasonic_sensors', 'camera'],
                'actuators': ['steering_assist', 'audio_warnings'],
                'update_interval_ms': 100,
                'priority': 'medium'
            },
            'navigation-basic': {
                'sensors': ['gps', 'traffic_data'],
                'actuators': ['display', 'audio'],
                'update_interval_ms': 1000,
                'priority': 'medium'
            }
        }
        
        self.config = self.apps_config.get(app_name, {
            'sensors': ['generic_sensor'],
            'actuators': ['generic_actuator'],
            'update_interval_ms': 1000,
            'priority': 'medium'
        })
        
    def simulate_sensors(self):
        """Simule les données des capteurs de confort"""
        sensor_data = {}
        for sensor in self.config.get('sensors', []):
            if sensor == 'interior_temp':
                sensor_data[sensor] = random.uniform(15, 30)  # °C
            elif sensor == 'exterior_temp':
                sensor_data[sensor] = random.uniform(-10, 40)  # °C
            elif sensor == 'humidity':
                sensor_data[sensor] = random.uniform(30, 80)  # %
            elif sensor == 'ambient_light':
                sensor_data[sensor] = random.uniform(0, 100)  # lux
            elif sensor == 'seat_position':
                sensor_data[sensor] = random.uniform(0, 100)  # % position
            elif sensor == 'ultrasonic_sensors':
                # Distance aux obstacles (parking)
                sensor_data[sensor] = [random.uniform(0.1, 5.0) for _ in range(8)]  # mètres
            else:
                sensor_data[sensor] = random.uniform(0, 1)  # valeur normalisée
        return sensor_data
    
    def process_comfort_logic(self, sensor_data):
        """Traite la logique de confort selon l'application"""
        actions = []
        
        if self.app_name == 'climate-control':
            interior_temp = sensor_data.get('interior_temp', 22)
            target_temp = 22  # Température cible
            if abs(interior_temp - target_temp) > 2:
                actions.append(f'HVAC_ADJUST_TO_{target_temp}C')
                
        elif self.app_name == 'seat-adjustment':
            # Simulation d'ajustement automatique
            if random.random() < 0.05:  # 5% chance d'ajustement
                actions.append('SEAT_POSITION_OPTIMIZED')
                
        elif self.app_name == 'lighting-control':
            ambient_light = sensor_data.get('ambient_light', 50)
            if ambient_light < 20:  # Faible luminosité
                actions.append('INTERIOR_LIGHTS_ON')
            elif ambient_light > 80:  # Forte luminosité
                actions.append('INTERIOR_LIGHTS_DIM')
                
        elif self.app_name == 'parking-assist':
            distances = sensor_data.get('ultrasonic_sensors', [5.0] * 8)
            min_distance = min(distances)
            if min_distance < 0.5:
                actions.append('PARKING_ALERT_VERY_CLOSE')
            elif min_distance < 1.0:
                actions.append('PARKING_WARNING')
                
        elif self.app_name == 'navigation-basic':
            # Simulation de recalcul de route
            if random.random() < 0.02:  # 2% chance de recalcul
                actions.append('ROUTE_RECALCULATED')
        
        return actions
    
    def run(self):
        """Boucle principale de simulation"""
        self.running = True
        self.metrics['start_time'] = datetime.now()
        
        print(f"[{datetime.now()}] Starting {self.app_name} comfort application")
        print(f"[{datetime.now()}] Priority: {self.config.get('priority', 'unknown')}")
        print(f"[{datetime.now()}] Update interval: {self.config.get('update_interval_ms', 0)}ms")
        
        update_interval = self.config.get('update_interval_ms', 1000) / 1000.0
        
        while self.running:
            cycle_start = time.time()
            
            # Simulation des capteurs
            sensor_data = self.simulate_sensors()
            
            # Traitement de la logique de confort
            actions = self.process_comfort_logic(sensor_data)
            
            if actions:
                self.metrics['adjustments'] += 1
                for action in actions:
                    print(f"[{datetime.now()}] {self.app_name}: 🔧 {action}")
            
            # Simulation de requêtes utilisateur
            if random.random() < 0.01:  # 1% chance de requête utilisateur
                self.metrics['user_requests'] += 1
                print(f"[{datetime.now()}] {self.app_name}: 👤 USER_REQUEST_PROCESSED")
            
            # Affichage statut normal périodique
            if self.metrics['cycles'] % 30 == 0:  # Toutes les 30 cycles
                uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
                print(f"[{datetime.now()}] {self.app_name}: ✅ Operating normally - "
                      f"Cycle {self.metrics['cycles']}, Uptime: {uptime:.1f}s, "
                      f"Adjustments: {self.metrics['adjustments']}, User requests: {self.metrics['user_requests']}")
            
            self.metrics['cycles'] += 1
            
            # Respecter l'intervalle de mise à jour
            cycle_time = time.time() - cycle_start
            sleep_time = max(0, update_interval - cycle_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

if __name__ == '__main__':
    app_name = os.environ.get('APP_NAME', 'climate-control')
    
    print("🏠 SDV Comfort Application Simulator")
    print("="*50)
    print(f"Application: {app_name}")
    print(f"Priority: {os.environ.get('SDV_PRIORITY', 'medium')}")
    print(f"Real-time mode: {os.environ.get('SDV_REAL_TIME', 'false')}")
    print(f"Pod: {os.environ.get('HOSTNAME', 'unknown')}")
    print("="*50)
    
    simulator = ComfortAppSimulator(app_name)
    
    try:
        simulator.run()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] {app_name} shutting down...")
        uptime = (datetime.now() - simulator.metrics['start_time']).total_seconds()
        print(f"[{datetime.now()}] Final metrics:")
        print(f"  • Uptime: {uptime:.1f}s")
        print(f"  • Cycles: {simulator.metrics['cycles']}")
        print(f"  • Adjustments: {simulator.metrics['adjustments']}")
        print(f"  • User requests: {simulator.metrics['user_requests']}")
        simulator.running = False 