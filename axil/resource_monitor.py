#!/usr/bin/env python3
"""
Resource Monitor - SDV Testbench
Module de surveillance des ressources pour les nœuds Raspberry Pi
Surveillance CPU, mémoire, réseau selon les contraintes TSN/TAS
"""

import time
import psutil
import subprocess
import json
import logging
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class NodeResourceMonitor:
    """Moniteur de ressources pour un nœud spécifique"""
    
    def __init__(self, node_name):
        self.node_name = node_name
        self.metrics_history = {
            'cpu': [],
            'memory': [],
            'network': [],
            'disk': []
        }
        
    def get_cpu_usage(self):
        """Récupère l'utilisation CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_history['cpu'].append({
                'timestamp': datetime.now(),
                'value': cpu_percent
            })
            return cpu_percent
        except Exception as e:
            logger.error(f"Erreur CPU monitoring {self.node_name}: {e}")
            return 0
    
    def get_memory_usage(self):
        """Récupère l'utilisation mémoire"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.metrics_history['memory'].append({
                'timestamp': datetime.now(),
                'value': memory_percent,
                'available_mb': memory.available / (1024*1024),
                'total_mb': memory.total / (1024*1024)
            })
            return memory_percent, memory.available / (1024*1024)
        except Exception as e:
            logger.error(f"Erreur Memory monitoring {self.node_name}: {e}")
            return 0, 0
    
    def get_network_usage(self):
        """Récupère l'utilisation réseau"""
        try:
            # Obtenir les statistiques réseau
            net_io = psutil.net_io_counters()
            
            # Calculer le débit (approximatif)
            if hasattr(self, '_last_net_io'):
                time_delta = time.time() - self._last_net_time
                bytes_sent_delta = net_io.bytes_sent - self._last_net_io.bytes_sent
                bytes_recv_delta = net_io.bytes_recv - self._last_net_io.bytes_recv
                
                # Convertir en Mbps
                send_mbps = (bytes_sent_delta * 8) / (time_delta * 1024 * 1024)
                recv_mbps = (bytes_recv_delta * 8) / (time_delta * 1024 * 1024)
                total_mbps = send_mbps + recv_mbps
            else:
                send_mbps = recv_mbps = total_mbps = 0
            
            self._last_net_io = net_io
            self._last_net_time = time.time()
            
            # Vérifier les contraintes TSN/TAS (10 Mbps)
            network_health = max(0, 100 - (total_mbps / 10 * 100))
            
            self.metrics_history['network'].append({
                'timestamp': datetime.now(),
                'send_mbps': send_mbps,
                'recv_mbps': recv_mbps,
                'total_mbps': total_mbps,
                'health': network_health
            })
            
            return total_mbps, network_health
            
        except Exception as e:
            logger.error(f"Erreur Network monitoring {self.node_name}: {e}")
            return 0, 100
    
    def get_disk_usage(self):
        """Récupère l'utilisation disque"""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            self.metrics_history['disk'].append({
                'timestamp': datetime.now(),
                'value': disk_percent,
                'free_gb': disk.free / (1024**3),
                'total_gb': disk.total / (1024**3)
            })
            
            return disk_percent, disk.free / (1024**3)
        except Exception as e:
            logger.error(f"Erreur Disk monitoring {self.node_name}: {e}")
            return 0, 0
    
    def check_resource_constraints(self, app_requirements):
        """Vérifie si le nœud peut satisfaire les contraintes d'une application"""
        cpu_usage = self.get_cpu_usage()
        memory_percent, memory_available_mb = self.get_memory_usage()
        network_mbps, network_health = self.get_network_usage()
        disk_percent, disk_free_gb = self.get_disk_usage()
        
        # Contraintes par défaut si non spécifiées
        required_cpu = app_requirements.get('cpu', 10)  # % CPU
        required_memory = app_requirements.get('memory', 50)  # MB
        required_network = app_requirements.get('bandwidth', 1)  # Mbps
        required_disk = app_requirements.get('disk', 0.1)  # GB
        
        # Vérifications
        cpu_ok = (100 - cpu_usage) >= required_cpu
        memory_ok = memory_available_mb >= required_memory
        network_ok = (10 - network_mbps) >= required_network  # Limite TSN/TAS 10Mbps
        disk_ok = disk_free_gb >= required_disk
        
        can_deploy = cpu_ok and memory_ok and network_ok and disk_ok
        
        constraints_status = {
            'can_deploy': can_deploy,
            'cpu': {'available': 100 - cpu_usage, 'required': required_cpu, 'ok': cpu_ok},
            'memory': {'available': memory_available_mb, 'required': required_memory, 'ok': memory_ok},
            'network': {'available': 10 - network_mbps, 'required': required_network, 'ok': network_ok},
            'disk': {'available': disk_free_gb, 'required': required_disk, 'ok': disk_ok},
            'network_health': network_health
        }
        
        return can_deploy, constraints_status
    
    def get_resource_summary(self):
        """Retourne un résumé des ressources actuelles"""
        cpu_usage = self.get_cpu_usage()
        memory_percent, memory_available_mb = self.get_memory_usage()
        network_mbps, network_health = self.get_network_usage()
        disk_percent, disk_free_gb = self.get_disk_usage()
        
        return {
            'node': self.node_name,
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'usage_percent': cpu_usage,
                'available_percent': 100 - cpu_usage
            },
            'memory': {
                'usage_percent': memory_percent,
                'available_mb': memory_available_mb
            },
            'network': {
                'usage_mbps': network_mbps,
                'available_mbps': 10 - network_mbps,  # TSN/TAS limit
                'health': network_health
            },
            'disk': {
                'usage_percent': disk_percent,
                'available_gb': disk_free_gb
            }
        }

class ClusterResourceMonitor:
    """Moniteur de ressources pour l'ensemble du cluster"""
    
    def __init__(self):
        self.node_monitors = {}
        self.cluster_metrics = []
        
        # Initialiser les moniteurs pour chaque type de nœud
        self.expected_nodes = ['orchestrator-node', 'node-safety', 'node-comfort', 'node-infotainment']
        for node_name in self.expected_nodes:
            self.node_monitors[node_name] = NodeResourceMonitor(node_name)
    
    def get_cluster_status(self):
        """Récupère le statut de l'ensemble du cluster"""
        cluster_status = {
            'timestamp': datetime.now().isoformat(),
            'nodes': {},
            'cluster_summary': {}
        }
        
        total_cpu_available = 0
        total_memory_available = 0
        total_network_available = 0
        node_count = 0
        
        for node_name, monitor in self.node_monitors.items():
            try:
                node_status = monitor.get_resource_summary()
                cluster_status['nodes'][node_name] = node_status
                
                # Agrégation pour résumé cluster
                total_cpu_available += node_status['cpu']['available_percent']
                total_memory_available += node_status['memory']['available_mb']
                total_network_available += node_status['network']['available_mbps']
                node_count += 1
                
            except Exception as e:
                logger.error(f"Erreur monitoring nœud {node_name}: {e}")
                cluster_status['nodes'][node_name] = {'error': str(e)}
        
        if node_count > 0:
            cluster_status['cluster_summary'] = {
                'avg_cpu_available': total_cpu_available / node_count,
                'total_memory_available_mb': total_memory_available,
                'total_network_available_mbps': total_network_available,
                'active_nodes': node_count,
                'expected_nodes': len(self.expected_nodes)
            }
        
        self.cluster_metrics.append(cluster_status)
        return cluster_status
    
    def find_best_node_for_app(self, app_requirements, preferred_zone=None):
        """Trouve le meilleur nœud pour déployer une application"""
        candidates = []
        
        for node_name, monitor in self.node_monitors.items():
            # Vérifier la zone préférée
            if preferred_zone:
                if preferred_zone == 'safety' and 'safety' not in node_name:
                    continue
                elif preferred_zone == 'comfort' and 'comfort' not in node_name:
                    continue
                elif preferred_zone == 'infotainment' and 'infotainment' not in node_name:
                    continue
                elif preferred_zone == 'orchestrator' and 'orchestrator' not in node_name:
                    continue
            
            try:
                can_deploy, constraints = monitor.check_resource_constraints(app_requirements)
                if can_deploy:
                    # Score basé sur les ressources disponibles
                    score = (
                        constraints['cpu']['available'] * 0.3 +
                        constraints['memory']['available'] * 0.001 +  # Normaliser MB vers %
                        constraints['network']['available'] * 10 +     # Normaliser Mbps vers %
                        constraints['network_health'] * 0.1
                    )
                    
                    candidates.append({
                        'node': node_name,
                        'score': score,
                        'constraints': constraints
                    })
            except Exception as e:
                logger.error(f"Erreur évaluation {node_name}: {e}")
        
        # Retourner le meilleur candidat
        if candidates:
            best_candidate = max(candidates, key=lambda x: x['score'])
            return best_candidate['node'], best_candidate['constraints']
        
        return None, None
    
    def check_cluster_health(self):
        """Vérifie la santé globale du cluster"""
        status = self.get_cluster_status()
        
        health_issues = []
        warnings = []
        
        for node_name, node_status in status['nodes'].items():
            if 'error' in node_status:
                health_issues.append(f"Nœud {node_name} non accessible")
                continue
            
            # Vérifications santé
            if node_status['cpu']['usage_percent'] > 90:
                health_issues.append(f"CPU critique sur {node_name}: {node_status['cpu']['usage_percent']:.1f}%")
            elif node_status['cpu']['usage_percent'] > 75:
                warnings.append(f"CPU élevé sur {node_name}: {node_status['cpu']['usage_percent']:.1f}%")
            
            if node_status['memory']['usage_percent'] > 90:
                health_issues.append(f"Mémoire critique sur {node_name}: {node_status['memory']['usage_percent']:.1f}%")
            elif node_status['memory']['usage_percent'] > 75:
                warnings.append(f"Mémoire élevée sur {node_name}: {node_status['memory']['usage_percent']:.1f}%")
            
            if node_status['network']['usage_mbps'] > 8:  # 80% de la limite TSN/TAS
                health_issues.append(f"Bande passante critique sur {node_name}: {node_status['network']['usage_mbps']:.1f}/10 Mbps")
            elif node_status['network']['usage_mbps'] > 6:
                warnings.append(f"Bande passante élevée sur {node_name}: {node_status['network']['usage_mbps']:.1f}/10 Mbps")
        
        health_score = max(0, 100 - len(health_issues) * 25 - len(warnings) * 10)
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score > 80 else 'warning' if health_score > 50 else 'critical',
            'issues': health_issues,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_metrics(self, filename=None):
        """Exporte les métriques collectées vers un fichier JSON"""
        if not filename:
            filename = f"/tmp/sdv_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'cluster_metrics': self.cluster_metrics,
            'node_metrics': {}
        }
        
        # Exporter les métriques détaillées de chaque nœud
        for node_name, monitor in self.node_monitors.items():
            export_data['node_metrics'][node_name] = monitor.metrics_history
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            logger.info(f"Métriques exportées vers: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Erreur export métriques: {e}")
            return None

# Fonction utilitaire pour monitoring en continu
def start_monitoring_daemon(interval=5, duration=300):
    """Démarre un daemon de monitoring pour le testbench SDV"""
    monitor = ClusterResourceMonitor()
    
    logger.info(f"Démarrage monitoring cluster SDV (durée: {duration}s, intervalle: {interval}s)")
    
    start_time = time.time()
    cycle = 0
    
    try:
        while time.time() - start_time < duration:
            cycle += 1
            cycle_start = time.time()
            
            # Collecte des métriques
            cluster_status = monitor.get_cluster_status()
            health = monitor.check_cluster_health()
            
            # Log résumé
            summary = cluster_status.get('cluster_summary', {})
            logger.info(f"Cycle {cycle} - CPU moy: {summary.get('avg_cpu_available', 0):.1f}% dispo, "
                       f"Santé: {health['health_score']}/100")
            
            # Attendre le prochain cycle
            cycle_time = time.time() - cycle_start
            sleep_time = max(0, interval - cycle_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("Monitoring arrêté par l'utilisateur")
    
    finally:
        # Export final des métriques
        export_file = monitor.export_metrics()
        total_time = time.time() - start_time
        logger.info(f"Monitoring terminé après {total_time:.1f}s ({cycle} cycles)")
        return export_file

if __name__ == '__main__':
    # Test du monitoring
    print("🔍 Resource Monitor - SDV Testbench")
    print("Test de monitoring des ressources du cluster\n")
    
    start_monitoring_daemon(interval=3, duration=30)
