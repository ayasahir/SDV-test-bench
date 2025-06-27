#!/usr/bin/env python3
"""
Vehicle Simulator - SDV Testbench
Simulateur d'état du véhicule pour tester l'orchestration dynamique AXIL
Génère des changements d'état réalistes selon les spécifications de la thèse
"""

import time
import random
import json
import logging
import threading
from datetime import datetime, timedelta
from enum import Enum
import math

logger = logging.getLogger(__name__)

class VehicleState(Enum):
    """États possibles du véhicule"""
    DRIVING = "driving"
    PARKING = "parking" 
    CHARGING = "charging"
    EMERGENCY = "emergency"

class VehicleEvent(Enum):
    """Événements véhicule"""
    ENGINE_START = "engine_start"
    ENGINE_STOP = "engine_stop"
    GEAR_CHANGE = "gear_change"
    BRAKE_APPLIED = "brake_applied"
    EMERGENCY_DETECTED = "emergency_detected"
    CHARGING_CONNECTED = "charging_connected"
    CHARGING_DISCONNECTED = "charging_disconnected"
    PARKING_INITIATED = "parking_initiated"

class VehicleParameters:
    """Paramètres du véhicule simulé"""
    
    def __init__(self):
        # Paramètres physiques
        self.speed = 0.0  # km/h
        self.fuel_level = random.uniform(20, 100)  # %
        self.battery_level = random.uniform(40, 100)  # %
        self.engine_temp = random.uniform(80, 95)  # °C
        self.gps_coords = [48.8566, 2.3522]  # Paris par défaut
        
        # Paramètres de conduite
        self.gear = 0
        self.rpm = 0
        self.brake_pressure = 0.0
        self.steering_angle = 0.0
        
        # Paramètres environnementaux
        self.outside_temp = random.uniform(-5, 35)  # °C
        self.weather = random.choice(['sunny', 'cloudy', 'rainy', 'snowy'])
        self.time_of_day = 'day'  # day/night
        
        # État des systèmes
        self.doors_locked = True
        self.lights_on = False
        self.ac_on = False
        self.radio_on = False

class VehicleSimulator:
    """Simulateur principal du véhicule"""
    
    def __init__(self, change_interval=10):
        self.current_state = VehicleState.PARKING
        self.parameters = VehicleParameters()
        self.change_interval = change_interval  # secondes
        self.running = False
        
        self.state_history = []
        self.event_history = []
        self.listeners = []  # Callbacks pour les changements d'état
        
        # Probabilités de transition entre états
        self.transition_probabilities = {
            VehicleState.PARKING: {
                VehicleState.DRIVING: 0.6,
                VehicleState.CHARGING: 0.25,
                VehicleState.EMERGENCY: 0.05,
                VehicleState.PARKING: 0.1
            },
            VehicleState.DRIVING: {
                VehicleState.PARKING: 0.4,
                VehicleState.EMERGENCY: 0.1,
                VehicleState.CHARGING: 0.05,
                VehicleState.DRIVING: 0.45
            },
            VehicleState.CHARGING: {
                VehicleState.PARKING: 0.7,
                VehicleState.DRIVING: 0.2,
                VehicleState.EMERGENCY: 0.05,
                VehicleState.CHARGING: 0.05
            },
            VehicleState.EMERGENCY: {
                VehicleState.PARKING: 0.6,
                VehicleState.DRIVING: 0.2,
                VehicleState.CHARGING: 0.1,
                VehicleState.EMERGENCY: 0.1
            }
        }
        
    def add_state_listener(self, callback):
        """Ajoute un callback appelé lors des changements d'état"""
        self.listeners.append(callback)
    
    def _notify_listeners(self, old_state, new_state):
        """Notifie tous les listeners d'un changement d'état"""
        for callback in self.listeners:
            try:
                callback(old_state, new_state, self.parameters)
            except Exception as e:
                logger.error(f"Erreur dans listener: {e}")
    
    def _update_parameters_for_state(self, state):
        """Met à jour les paramètres selon l'état actuel"""
        if state == VehicleState.DRIVING:
            self.parameters.speed = random.uniform(30, 120)
            self.parameters.rpm = int(random.uniform(1500, 4000))
            self.parameters.gear = random.randint(2, 5)
            self.parameters.brake_pressure = random.uniform(0, 20)
            self.parameters.steering_angle = random.uniform(-30, 30)
            self.parameters.fuel_level = max(0, self.parameters.fuel_level - random.uniform(0.1, 0.5))
            
        elif state == VehicleState.PARKING:
            self.parameters.speed = 0
            self.parameters.rpm = 0
            self.parameters.gear = 0
            self.parameters.brake_pressure = 100
            self.parameters.steering_angle = 0
            self.parameters.doors_locked = True
            
        elif state == VehicleState.CHARGING:
            self.parameters.speed = 0
            self.parameters.rpm = 0
            self.parameters.gear = 0
            self.parameters.battery_level = min(100, self.parameters.battery_level + random.uniform(1, 5))
            self.parameters.ac_on = random.choice([True, False])
            
        elif state == VehicleState.EMERGENCY:
            self.parameters.brake_pressure = 100
            self.parameters.lights_on = True
            # Speed peut varier selon le type d'urgence
            self.parameters.speed = random.uniform(0, self.parameters.speed * 0.3)
    
    def _generate_random_event(self):
        """Génère un événement aléatoire selon l'état actuel"""
        events_by_state = {
            VehicleState.DRIVING: [
                VehicleEvent.GEAR_CHANGE,
                VehicleEvent.BRAKE_APPLIED,
                VehicleEvent.EMERGENCY_DETECTED
            ],
            VehicleState.PARKING: [
                VehicleEvent.ENGINE_START,
                VehicleEvent.CHARGING_CONNECTED
            ],
            VehicleState.CHARGING: [
                VehicleEvent.CHARGING_DISCONNECTED,
                VehicleEvent.ENGINE_START
            ],
            VehicleState.EMERGENCY: [
                VehicleEvent.BRAKE_APPLIED,
                VehicleEvent.ENGINE_STOP
            ]
        }
        
        possible_events = events_by_state.get(self.current_state, [])
        if possible_events and random.random() < 0.3:  # 30% chance d'événement
            event = random.choice(possible_events)
            self.event_history.append({
                'timestamp': datetime.now(),
                'event': event.value,
                'state': self.current_state.value,
                'parameters': self._get_current_parameters_dict()
            })
            logger.info(f"🎯 Événement généré: {event.value} en état {self.current_state.value}")
            return event
        return None
    
    def _choose_next_state(self):
        """Choisit le prochain état selon les probabilités de transition"""
        probabilities = self.transition_probabilities[self.current_state]
        
        # Ajustements contextuels des probabilités
        adjusted_probs = probabilities.copy()
        
        # Facteurs influençant les transitions
        if self.parameters.fuel_level < 20 and self.parameters.battery_level < 30:
            # Favoriser le charging si batterie et carburant faibles
            adjusted_probs[VehicleState.CHARGING] *= 2
            
        if self.parameters.speed > 100:
            # Plus de risque d'urgence à haute vitesse
            adjusted_probs[VehicleState.EMERGENCY] *= 1.5
            
        # Normaliser les probabilités
        total = sum(adjusted_probs.values())
        for state in adjusted_probs:
            adjusted_probs[state] /= total
        
        # Sélection aléatoire pondérée
        rand = random.random()
        cumulative = 0
        for state, prob in adjusted_probs.items():
            cumulative += prob
            if rand <= cumulative:
                return state
        
        return self.current_state  # Fallback
    
    def _get_current_parameters_dict(self):
        """Retourne les paramètres actuels sous forme de dictionnaire"""
        return {
            'speed': self.parameters.speed,
            'fuel_level': self.parameters.fuel_level,
            'battery_level': self.parameters.battery_level,
            'engine_temp': self.parameters.engine_temp,
            'gps_coords': self.parameters.gps_coords,
            'gear': self.parameters.gear,
            'rpm': self.parameters.rpm,
            'brake_pressure': self.parameters.brake_pressure,
            'steering_angle': self.parameters.steering_angle,
            'outside_temp': self.parameters.outside_temp,
            'weather': self.parameters.weather,
            'doors_locked': self.parameters.doors_locked,
            'lights_on': self.parameters.lights_on,
            'ac_on': self.parameters.ac_on,
            'radio_on': self.parameters.radio_on
        }
    
    def change_state(self, new_state=None):
        """Change l'état du véhicule"""
        old_state = self.current_state
        
        if new_state is None:
            new_state = self._choose_next_state()
        
        if new_state != old_state:
            self.current_state = new_state
            self._update_parameters_for_state(new_state)
            
            # Enregistrer le changement
            state_change = {
                'timestamp': datetime.now(),
                'old_state': old_state.value,
                'new_state': new_state.value,
                'parameters': self._get_current_parameters_dict()
            }
            self.state_history.append(state_change)
            
            logger.info(f"🚗 État changé: {old_state.value} → {new_state.value}")
            
            # Notifier les listeners
            self._notify_listeners(old_state, new_state)
            
            return True
        return False
    
    def get_current_state(self):
        """Retourne l'état actuel"""
        return self.current_state.value
    
    def get_current_parameters(self):
        """Retourne les paramètres actuels"""
        return self._get_current_parameters_dict()
    
    def get_vehicle_status(self):
        """Retourne un statut complet du véhicule"""
        return {
            'state': self.current_state.value,
            'parameters': self._get_current_parameters_dict(),
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': time.time() - getattr(self, '_start_time', time.time())
        }
    
    def start_simulation(self, duration=60):
        """Démarre la simulation pour une durée donnée (en secondes)"""
        self.running = True
        self._start_time = time.time()
        
        logger.info(f" Simulation véhicule démarrée (durée: {duration}s, changements: {self.change_interval}s)")
        
        def simulation_loop():
            cycles = 0
            while self.running and (time.time() - self._start_time) < duration:
                cycles += 1
                cycle_start = time.time()
                
                # Changement d'état selon l'intervalle
                if cycles == 1 or (time.time() - self._start_time) % self.change_interval < 1:
                    self.change_state()
                
                # Génération d'événements aléatoires
                self._generate_random_event()
                
                # Mise à jour continue des paramètres
                self._update_continuous_parameters()
                
                # Attendre le prochain cycle
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, 1 - cycle_time)  # Cycle chaque seconde
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            self.running = False
            logger.info(f"🏁 Simulation terminée après {cycles} cycles")
        
        # Démarrer en thread séparé
        self.simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        self.simulation_thread.start()
    
    def _update_continuous_parameters(self):
        """Met à jour les paramètres qui évoluent en continu"""
        # Usure du carburant en conduite
        if self.current_state == VehicleState.DRIVING:
            fuel_consumption = 0.01 * (self.parameters.speed / 100)
            self.parameters.fuel_level = max(0, self.parameters.fuel_level - fuel_consumption)
        
        # Charge de la batterie
        if self.current_state == VehicleState.CHARGING:
            charge_rate = random.uniform(0.1, 0.3)
            self.parameters.battery_level = min(100, self.parameters.battery_level + charge_rate)
        
        # Température moteur
        if self.current_state == VehicleState.DRIVING:
            temp_increase = random.uniform(-0.5, 1.0)
            self.parameters.engine_temp = max(70, min(120, self.parameters.engine_temp + temp_increase))
        else:
            # Refroidissement quand arrêté
            temp_decrease = random.uniform(0, 0.5)
            self.parameters.engine_temp = max(self.parameters.outside_temp + 10, 
                                            self.parameters.engine_temp - temp_decrease)
    
    def stop_simulation(self):
        """Arrête la simulation"""
        self.running = False
        if hasattr(self, 'simulation_thread'):
            self.simulation_thread.join(timeout=2)
        logger.info(" Simulation véhicule arrêtée")
    
    def export_history(self, filename=None):
        """Exporte l'historique de simulation"""
        if not filename:
            filename = f"/tmp/vehicle_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'simulation_info': {
                'start_time': getattr(self, '_start_time', time.time()),
                'duration': time.time() - getattr(self, '_start_time', time.time()),
                'change_interval': self.change_interval
            },
            'state_history': self.state_history,
            'event_history': self.event_history,
            'final_state': self.get_vehicle_status()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            logger.info(f"Historique véhicule exporté vers: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Erreur export historique: {e}")
            return None

# Classe pour testing patterns spécifiques
class TestScenarioSimulator(VehicleSimulator):
    """Simulateur avec scénarios de test prédéfinis"""
    
    def __init__(self):
        super().__init__(change_interval=10)
        
    def run_thesis_scenario(self):
        """Reproduit le scénario exact de la thèse: 60s avec changements toutes les 10s"""
        logger.info("🎓 Exécution du scénario de thèse (60s, changements toutes les 10s)")
        
        # Séquence d'états prédéfinie pour reproductibilité
        test_sequence = [
            VehicleState.PARKING,    # 0-10s
            VehicleState.DRIVING,    # 10-20s  
            VehicleState.EMERGENCY,  # 20-30s
            VehicleState.PARKING,    # 30-40s
            VehicleState.CHARGING,   # 40-50s
            VehicleState.DRIVING     # 50-60s
        ]
        
        def thesis_scenario():
            start_time = time.time()
            sequence_index = 0
            
            while (time.time() - start_time) < 60 and sequence_index < len(test_sequence):
                elapsed = time.time() - start_time
                expected_change_time = sequence_index * 10
                
                if elapsed >= expected_change_time:
                    new_state = test_sequence[sequence_index]
                    self.change_state(new_state)
                    sequence_index += 1
                
                time.sleep(1)
            
            logger.info(" Scénario de thèse terminé")
        
        # Démarrer le scénario
        self.running = True
        thesis_thread = threading.Thread(target=thesis_scenario, daemon=True)
        thesis_thread.start()
        thesis_thread.join()

if __name__ == '__main__':
    # Test du simulateur
    print("Vehicle Simulator - SDV Testbench")
    print("Test de simulation d'état véhicule\n")
    
    # Callback d'exemple
    def on_state_change(old_state, new_state, parameters):
        print(f"Callback: {old_state.value} → {new_state.value} "
              f"(vitesse: {parameters.speed:.1f} km/h)")
    
    # Test scénario normal
    simulator = VehicleSimulator(change_interval=5)
    simulator.add_state_listener(on_state_change)
    simulator.start_simulation(duration=30)
    
    # Attendre la fin
    while simulator.running:
        time.sleep(1)
    
    # Export des résultats
    export_file = simulator.export_history()
    print(f"\nRésultats exportés: {export_file}")
    
    print("\n" + "="*50)
    print("Test du scénario de thèse:")
    
    # Test scénario thèse
    test_sim = TestScenarioSimulator()
    test_sim.add_state_listener(on_state_change)
    test_sim.run_thesis_scenario()
    test_sim.export_history()
