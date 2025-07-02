#!/usr/bin/env python3
"""
AXIL Orchestrator - SDV Testbench
Gère les états du véhicule, les ressources et le déploiement des applis Kubernetes  
Nécessite un cluster Kubernetes activé (utiliser run_baseline_local.sh)
"""

import time
import random
import json
import logging
import threading
import yaml
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import psutil
import subprocess
import os
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/axil.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VehicleStateManager:
    """Initialise l'état avec "paring" avec un intervalle de changement d'état 
    de 10 secondes"""
    def __init__(self):
        self.states = ['driving', 'parking', 'charging', 'emergency']
        self.current_state = 'parking'
        self.state_change_interval = 10  # secondes
        self.running = True

    """Retourne l'état actuel du véhicule"""
    def get_current_state(self):
        return self.current_state
    
    """Change l'état du véhicule de manière aléatoire"""
    def change_state_randomly(self):
        old_state = self.current_state
        self.current_state = random.choice(self.states)
        if old_state != self.current_state:
            logger.info(f" État véhicule changé: {old_state} → {self.current_state}")
        return self.current_state
    
    """Démarre le monitoring d'état en arrière-plan"""
    def start_state_monitor(self):
        
        def state_loop():
            while self.running:
                time.sleep(self.state_change_interval)
                if self.running:
                    self.change_state_randomly()
        
        thread = threading.Thread(target=state_loop, daemon=True)
        thread.start()
        logger.info(f" Monitoring d'état démarré (changement toutes les {self.state_change_interval}s)")

"""Moniteur de ressources pour les nœuds du cluster"""
class ResourceMonitor:
    
    
    def __init__(self):
        self.nodes_resources = {}
        
    """Récupère les ressources disponibles d'un nœud"""
    def get_node_resources(self, node_name):
        
        try:
            # Simulation des ressources (en production, utiliser metrics-server)
            cpu_percent = random.uniform(20, 80)  # Simulation CPU usage
            memory_percent = random.uniform(30, 70)  # Simulation memory usage
            
            return {
                'cpu_available': 100 - cpu_percent,
                'memory_available': 100 - memory_percent,
                'network_bandwidth': random.uniform(5, 10)  # Mbps disponible
            }
        except Exception as e:
            logger.error(f"Erreur récupération ressources {node_name}: {e}")
            return {'cpu_available': 50, 'memory_available': 50, 'network_bandwidth': 5}
    
    """Vérifie si un nœud peut héberger une application"""
    def check_resource_constraints(self, node_name, app_requirements):
        
        resources = self.get_node_resources(node_name)
        
        can_deploy = (
            resources['cpu_available'] >= app_requirements.get('cpu', 10) and
            resources['memory_available'] >= app_requirements.get('memory', 10) and
            resources['network_bandwidth'] >= app_requirements.get('bandwidth', 1)
        )
        
        return can_deploy, resources

"""Gestionnaire des applications SDV"""
class ApplicationManager:
    
    def __init__(self):
        self.apps_config = self._load_apps_configuration()
        self.deployed_apps = {}

    """Charge la configuration des 30 applications"""   
    def _load_apps_configuration(self):
        
        apps = []
        
        # Applications Safety (priorité haute)
        safety_apps = [
            {'name': 'emergency-brake', 'priority': 1, 'cpu': 15, 'memory': 20, 'bandwidth': 2},
            {'name': 'collision-avoidance', 'priority': 1, 'cpu': 20, 'memory': 25, 'bandwidth': 3},
            {'name': 'lane-keeping', 'priority': 2, 'cpu': 12, 'memory': 15, 'bandwidth': 1.5},
            {'name': 'adaptive-cruise', 'priority': 2, 'cpu': 18, 'memory': 22, 'bandwidth': 2.5},
            {'name': 'driver-monitoring', 'priority': 1, 'cpu': 10, 'memory': 18, 'bandwidth': 1},
            {'name': 'traffic-sign-detection', 'priority': 2, 'cpu': 25, 'memory': 30, 'bandwidth': 2},
            {'name': 'pedestrian-detection', 'priority': 1, 'cpu': 22, 'memory': 28, 'bandwidth': 2.5},
            {'name': 'vehicle-tracking', 'priority': 2, 'cpu': 16, 'memory': 20, 'bandwidth': 1.8},
            {'name': 'emergency-call', 'priority': 1, 'cpu': 5, 'memory': 10, 'bandwidth': 0.5},
            {'name': 'airbag-control', 'priority': 1, 'cpu': 8, 'memory': 12, 'bandwidth': 0.3}
        ]
        
        # Applications Comfort (priorité moyenne)
        comfort_apps = [
            {'name': 'climate-control', 'priority': 3, 'cpu': 8, 'memory': 12, 'bandwidth': 0.5},
            {'name': 'seat-adjustment', 'priority': 4, 'cpu': 5, 'memory': 8, 'bandwidth': 0.2},
            {'name': 'lighting-control', 'priority': 3, 'cpu': 6, 'memory': 10, 'bandwidth': 0.3},
            {'name': 'mirror-adjustment', 'priority': 4, 'cpu': 4, 'memory': 6, 'bandwidth': 0.2},
            {'name': 'parking-assist', 'priority': 3, 'cpu': 15, 'memory': 20, 'bandwidth': 1.5},
            {'name': 'navigation-basic', 'priority': 3, 'cpu': 12, 'memory': 18, 'bandwidth': 1},
            {'name': 'voice-commands', 'priority': 3, 'cpu': 10, 'memory': 15, 'bandwidth': 0.8},
            {'name': 'gesture-control', 'priority': 4, 'cpu': 14, 'memory': 16, 'bandwidth': 0.6},
            {'name': 'ambient-lighting', 'priority': 4, 'cpu': 3, 'memory': 5, 'bandwidth': 0.1},
            {'name': 'massage-seats', 'priority': 4, 'cpu': 6, 'memory': 8, 'bandwidth': 0.2}
        ]
        
        # Applications Infotainment (priorité basse)
        infotainment_apps = [
            {'name': 'media-player', 'priority': 5, 'cpu': 15, 'memory': 25, 'bandwidth': 2},
            {'name': 'streaming-video', 'priority': 5, 'cpu': 25, 'memory': 40, 'bandwidth': 5},
            {'name': 'games-engine', 'priority': 5, 'cpu': 30, 'memory': 50, 'bandwidth': 3},
            {'name': 'social-media', 'priority': 5, 'cpu': 12, 'memory': 20, 'bandwidth': 2.5},
            {'name': 'web-browser', 'priority': 5, 'cpu': 20, 'memory': 35, 'bandwidth': 3.5},
            {'name': 'music-streaming', 'priority': 4, 'cpu': 8, 'memory': 15, 'bandwidth': 1.5},
            {'name': 'video-calls', 'priority': 4, 'cpu': 18, 'memory': 28, 'bandwidth': 4},
            {'name': 'ar-navigation', 'priority': 4, 'cpu': 35, 'memory': 45, 'bandwidth': 4.5},
            {'name': 'news-reader', 'priority': 5, 'cpu': 6, 'memory': 12, 'bandwidth': 1},
            {'name': 'weather-app', 'priority': 5, 'cpu': 4, 'memory': 8, 'bandwidth': 0.5}
        ]
        
        # Assignation des zones
        for app in safety_apps:
            app['zone'] = 'safety'
            app['category'] = 'safety'
        for app in comfort_apps:
            app['zone'] = 'comfort'
            app['category'] = 'comfort'
        for app in infotainment_apps:
            app['zone'] = 'infotainment'
            app['category'] = 'infotainment'
        
        apps.extend(safety_apps)
        apps.extend(comfort_apps)
        apps.extend(infotainment_apps)
        
        logger.info(f" Configuration chargée: {len(apps)} applications")
        return apps
    
    def get_apps_for_state(self, vehicle_state):
        """Retourne les applications nécessaires selon l'état du véhicule"""
        state_mapping = {
            'driving': {
                'safety': ['emergency-brake', 'collision-avoidance', 'lane-keeping', 
                          'adaptive-cruise', 'driver-monitoring', 'traffic-sign-detection',
                          'pedestrian-detection', 'vehicle-tracking'],
                'comfort': ['climate-control', 'navigation-basic', 'voice-commands'],
                'infotainment': ['music-streaming']
            },
            'parking': {
                'safety': ['emergency-brake', 'driver-monitoring', 'emergency-call'],
                'comfort': ['climate-control', 'seat-adjustment', 'lighting-control',
                           'mirror-adjustment', 'parking-assist'],
                'infotainment': ['media-player', 'social-media', 'web-browser', 'news-reader']
            },
            'charging': {
                'safety': ['emergency-call', 'airbag-control'],
                'comfort': ['climate-control', 'seat-adjustment', 'ambient-lighting', 'massage-seats'],
                'infotainment': ['streaming-video', 'games-engine', 'video-calls', 'ar-navigation', 'weather-app']
            },
            'emergency': {
                'safety': ['emergency-brake', 'collision-avoidance', 'driver-monitoring',
                          'emergency-call', 'airbag-control'],
                'comfort': [],
                'infotainment': []
            }
        }
        
        return state_mapping.get(vehicle_state, {'safety': [], 'comfort': [], 'infotainment': []})

"""Orchestrateur principal AXIL pour SDV"""
class AXILOrchestrator:
   
    
    def __init__(self):
        self.vehicle_state_manager = VehicleStateManager()
        self.resource_monitor = ResourceMonitor()
        self.app_manager = ApplicationManager()
        self.metrics = {
            'deployments': 0,
            'failures': 0,
            'optimization_time': [],
            'network_health': [],
            'resource_usage': []
        }
        
        # Initialisation Kubernetes
        try:
            config.load_kube_config()
            self.k8s_apps = client.AppsV1Api()
            self.k8s_core = client.CoreV1Api()
            logger.info(" Connexion Kubernetes établie")
        except Exception as e:
            logger.error(f" Erreur connexion Kubernetes: {e}")
            sys.exit(1)
    
    """Algorithme d'optimisation des déploiements selon l'état du véhicule"""
    def optimize_deployments(self):
        
        start_time = time.time()
        
        current_state = self.vehicle_state_manager.get_current_state()
        required_apps = self.app_manager.get_apps_for_state(current_state)
        
        logger.info(f"Optimisation pour état: {current_state}")
        
        deployment_plan = {}
        total_network_usage = 0
        
        # Planification par ordre de priorité
        all_required_apps = []
        for zone, app_names in required_apps.items():
            for app_name in app_names:
                app_config = next((app for app in self.app_manager.apps_config 
                                 if app['name'] == app_name), None)
                if app_config:
                    all_required_apps.append((zone, app_config))
        
        # Tri par priorité (1 = plus haute priorité)
        all_required_apps.sort(key=lambda x: x[1]['priority'])
        
        # Déploiement avec contraintes
        for zone, app_config in all_required_apps:
            node_name = f"node-{zone}"
            
            # Vérifier les contraintes réseau globales (10Mbps TAS limit)
            if total_network_usage + app_config['bandwidth'] > 10:
                logger.warning(f"App {app_config['name']} ignorée: limite réseau TAS atteinte")
                continue
            
            # Vérifier les contraintes de ressources du nœud
            can_deploy, resources = self.resource_monitor.check_resource_constraints(
                node_name, app_config
            )
            
            if can_deploy:
                if zone not in deployment_plan:
                    deployment_plan[zone] = []
                deployment_plan[zone].append(app_config)
                total_network_usage += app_config['bandwidth']
                logger.info(f"✓ {app_config['name']} planifié sur {zone}")
            else:
                logger.warning(f"⚠️  {app_config['name']} rejeté: ressources insuffisantes sur {zone}")
        
        optimization_time = time.time() - start_time
        self.metrics['optimization_time'].append(optimization_time)
        
        logger.info(f" Temps d'optimisation: {optimization_time:.2f}s")
        logger.info(f" Utilisation réseau totale: {total_network_usage:.1f}/10.0 Mbps")
        
        return deployment_plan, total_network_usage
    
    def deploy_applications(self, deployment_plan):
        """Déploie les applications selon le plan d'optimisation"""
        deployed_count = 0
        
        for zone, apps in deployment_plan.items():
            for app_config in apps:
                try:
                    if self._deploy_single_app(app_config, zone):
                        deployed_count += 1
                        self.metrics['deployments'] += 1
                except Exception as e:
                    logger.error(f"✗ Erreur déploiement {app_config['name']}: {e}")
                    self.metrics['failures'] += 1
        
        logger.info(f" Applications déployées: {deployed_count}")
        return deployed_count
    
    def _deploy_single_app(self, app_config, zone):
        """Déploie une application sur un nœud spécifique"""
        app_name = app_config['name']
        
        # Création du manifeste Kubernetes
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=f"sdv-{app_name}",
                namespace="default",
                labels={
                    "app": app_name,
                    "zone": zone,
                    "category": app_config['category'],
                    "priority": str(app_config['priority'])
                }
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": app_name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": app_name, "zone": zone}
                    ),
                    spec=client.V1PodSpec(
                        node_selector={"zone": zone},
                        containers=[
                            client.V1Container(
                                name=app_name,
                                image="busybox:latest",
                                command=["sh", "-c"],
                                args=[f"while true; do echo '[{datetime.now()}] {app_name} running on {zone}'; sleep 5; done"],
                                resources=client.V1ResourceRequirements(
                                    requests={
                                        "cpu": f"{app_config['cpu']}m",
                                        "memory": f"{app_config['memory']}Mi"
                                    },
                                    limits={
                                        "cpu": f"{app_config['cpu']*2}m",
                                        "memory": f"{app_config['memory']*2}Mi"
                                    }
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        try:
            # Supprimer l'ancien déploiement s'il existe
            try:
                self.k8s_apps.delete_namespaced_deployment(
                    name=f"sdv-{app_name}",
                    namespace="default"
                )
                time.sleep(1)
            except ApiException:
                pass  # L'app n'existait pas
            
            # Créer le nouveau déploiement
            self.k8s_apps.create_namespaced_deployment(
                namespace="default",
                body=deployment
            )
            
            logger.debug(f" {app_name} déployé sur {zone}")
            return True
            
        except ApiException as e:
            logger.error(f" Erreur K8s pour {app_name}: {e}")
            return False
    
    def collect_metrics(self):
        """Collecte les métriques de performance"""
        try:
            # Métriques réseau (simulation)
            network_health = random.uniform(75, 95)  # % de santé réseau
            self.metrics['network_health'].append(network_health)
            
            # Métriques de ressources
            pods = self.k8s_core.list_pod_for_all_namespaces()
            running_pods = len([p for p in pods.items if p.status.phase == "Running"])
            resource_usage = min(100, (running_pods / 30) * 100)  # % d'utilisation
            self.metrics['resource_usage'].append(resource_usage)
            
            logger.info(f" Métriques - Réseau: {network_health:.1f}%, Ressources: {resource_usage:.1f}%")
            
        except Exception as e:
            logger.error(f"Erreur collecte métriques: {e}")
    
    def cleanup_unused_apps(self):
        """Nettoie les applications non nécessaires"""
        try:
            deployments = self.k8s_apps.list_namespaced_deployment(namespace="default")
            current_state = self.vehicle_state_manager.get_current_state()
            required_apps = self.app_manager.get_apps_for_state(current_state)
            
            # Liste des apps requises
            all_required = []
            for app_list in required_apps.values():
                all_required.extend(app_list)
            
            cleaned = 0
            for deployment in deployments.items:
                if deployment.metadata.name.startswith("sdv-"):
                    app_name = deployment.metadata.name[4:]  # Enlever "sdv-"
                    if app_name not in all_required:
                        self.k8s_apps.delete_namespaced_deployment(
                            name=deployment.metadata.name,
                            namespace="default"
                        )
                        cleaned += 1
                        logger.info(f"  App {app_name} supprimée (non requise)")
            
            if cleaned > 0:
                logger.info(f" {cleaned} applications nettoyées")
                
        except Exception as e:
            logger.error(f"Erreur nettoyage: {e}")
    
    def print_status(self):
        """Affiche le statut du système"""
        current_state = self.vehicle_state_manager.get_current_state()
        
        try:
            pods = self.k8s_core.list_pod_for_all_namespaces()
            running_pods = len([p for p in pods.items if p.status.phase == "Running" and p.metadata.name.startswith("sdv-")])
            
            avg_opt_time = sum(self.metrics['optimization_time'][-5:]) / min(5, len(self.metrics['optimization_time'])) if self.metrics['optimization_time'] else 0
            
            print(f"\n{'='*60}")
            print(f" État véhicule: {current_state.upper()}")
            print(f" Applications actives: {running_pods}/30")
            print(f" Temps optimisation moyen: {avg_opt_time:.2f}s")
            print(f" Déploiements réussis: {self.metrics['deployments']}")
            print(f" Échecs: {self.metrics['failures']}")
            if self.metrics['network_health']:
                print(f" Santé réseau: {self.metrics['network_health'][-1]:.1f}%")
            print(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Erreur affichage statut: {e}")
    
    def run(self):
        """Boucle principale AXIL - Test de 60 secondes avec changements toutes les 10s"""
        logger.info(" AXIL Orchestrator démarré - Test SDV de 60 secondes")
        
        # Démarrer le monitoring d'état
        self.vehicle_state_manager.start_state_monitor()
        
        start_time = time.time()
        test_duration = 60  # 60 secondes comme dans la thèse
        cycle_count = 0
        
        try:
            while time.time() - start_time < test_duration:
                cycle_count += 1
                cycle_start = time.time()
                
                logger.info(f"\n === CYCLE {cycle_count} ===")
                
                # Optimisation et déploiement
                deployment_plan, network_usage = self.optimize_deployments()
                self.deploy_applications(deployment_plan)
                
                # Nettoyage des apps non nécessaires
                self.cleanup_unused_apps()
                
                # Collecte des métriques
                self.collect_metrics()
                
                # Affichage du statut
                self.print_status()
                
                # Attendre le prochain cycle (environ 5-10 secondes)
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, 8 - cycle_time)  # Cycle toutes les ~8 secondes
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info(" Arrêt demandé par l'utilisateur")
        
        finally:
            self.vehicle_state_manager.running = False
            
            # Rapport final
            total_time = time.time() - start_time
            logger.info(f"\n === RAPPORT FINAL SDV TESTBENCH ===")
            logger.info(f" Durée totale: {total_time:.1f}s")
            logger.info(f" Cycles exécutés: {cycle_count}")
            logger.info(f" Déploiements totaux: {self.metrics['deployments']}")
            logger.info(f" Échecs: {self.metrics['failures']}")
            logger.info(f" Temps optimisation moyen: {sum(self.metrics['optimization_time'])/len(self.metrics['optimization_time']):.2f}s")
            
            if self.metrics['network_health']:
                avg_network = sum(self.metrics['network_health']) / len(self.metrics['network_health'])
                logger.info(f" Santé réseau moyenne: {avg_network:.1f}%")
            
            logger.info("Test SDV terminé")

if __name__ == '__main__':
    print(" AXIL Orchestrator pour SDV Testbench")
    print("Basé sur la thèse - Test de 60 secondes avec changements d'état")
    print("Ctrl+C pour arrêter\n")
    
    orchestrator = AXILOrchestrator()
    orchestrator.run()
