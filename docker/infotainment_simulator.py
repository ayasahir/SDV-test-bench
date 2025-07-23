#!/usr/bin/env python3
"""
SDV Infotainment Application Simulator
Simule les applications d'entertainment et d'information véhicule
"""

import os
import time
import random
import threading
from datetime import datetime

class InfotainmentAppSimulator:
    def __init__(self, app_name):
        self.app_name = app_name
        self.running = False
        self.metrics = {
            'start_time': None,
            'cycles': 0,
            'content_played': 0,
            'user_interactions': 0,
            'data_processed_mb': 0
        }
        
        # Configuration des applications infotainment
        self.apps_config = {
            'media-player': {
                'content_types': ['music', 'podcast', 'audiobook'],
                'bandwidth_mbps': 2.0,
                'update_interval_ms': 1000,
                'priority': 'low'
            },
            'streaming-video': {
                'content_types': ['movies', 'series', 'youtube'],
                'bandwidth_mbps': 5.0,
                'update_interval_ms': 500,
                'priority': 'low'
            },
            'games-engine': {
                'content_types': ['puzzle', 'arcade', 'simulation'],
                'bandwidth_mbps': 3.0,
                'update_interval_ms': 16,  # 60 FPS
                'priority': 'low'
            },
            'social-media': {
                'content_types': ['feed', 'messages', 'notifications'],
                'bandwidth_mbps': 2.5,
                'update_interval_ms': 2000,
                'priority': 'low'
            },
            'web-browser': {
                'content_types': ['web_pages', 'search', 'news'],
                'bandwidth_mbps': 3.5,
                'update_interval_ms': 1000,
                'priority': 'low'
            },
            'music-streaming': {
                'content_types': ['spotify', 'radio', 'local_music'],
                'bandwidth_mbps': 1.5,
                'update_interval_ms': 1000,
                'priority': 'medium'
            }
        }
        
        self.config = self.apps_config.get(app_name, {
            'content_types': ['generic_content'],
            'bandwidth_mbps': 1.0,
            'update_interval_ms': 1000,
            'priority': 'low'
        })
        
    def simulate_content_processing(self):
        """Simule le traitement de contenu multimédia"""
        content_info = {}
        content_types = self.config.get('content_types', ['generic'])
        current_content = random.choice(content_types)
        
        if self.app_name == 'media-player':
            content_info = {
                'type': current_content,
                'duration_sec': random.randint(120, 300),
                'quality': random.choice(['128kbps', '320kbps', 'lossless']),
                'buffer_level': random.uniform(70, 100)
            }
        elif self.app_name == 'streaming-video':
            content_info = {
                'type': current_content,
                'resolution': random.choice(['720p', '1080p', '4K']),
                'framerate': random.choice([24, 30, 60]),
                'buffer_level': random.uniform(60, 100)
            }
        elif self.app_name == 'games-engine':
            content_info = {
                'type': current_content,
                'fps': random.uniform(30, 60),
                'gpu_load': random.uniform(40, 90),
                'physics_objects': random.randint(10, 100)
            }
        elif self.app_name == 'social-media':
            content_info = {
                'type': current_content,
                'new_posts': random.randint(0, 5),
                'notifications': random.randint(0, 3),
                'network_requests': random.randint(5, 20)
            }
        elif self.app_name == 'web-browser':
            content_info = {
                'type': current_content,
                'tabs_open': random.randint(1, 8),
                'page_load_time': random.uniform(0.5, 3.0),
                'javascript_active': random.choice([True, False])
            }
        elif self.app_name == 'music-streaming':
            content_info = {
                'type': current_content,
                'bitrate': random.choice(['128', '256', '320']),
                'playlist_length': random.randint(10, 50),
                'download_progress': random.uniform(0, 100)
            }
        
        return content_info
    
    def process_user_interactions(self):
        """Simule les interactions utilisateur"""
        interactions = []
        
        # Simulation d'interactions aléatoires
        if random.random() < 0.05:  # 5% chance d'interaction
            if self.app_name in ['media-player', 'music-streaming']:
                interactions.append(random.choice(['PLAY', 'PAUSE', 'NEXT_TRACK', 'VOLUME_CHANGE']))
            elif self.app_name == 'streaming-video':
                interactions.append(random.choice(['PLAY', 'PAUSE', 'SEEK', 'QUALITY_CHANGE']))
            elif self.app_name == 'games-engine':
                interactions.append(random.choice(['TOUCH_INPUT', 'MENU_NAVIGATION', 'GAME_ACTION']))
            elif self.app_name == 'social-media':
                interactions.append(random.choice(['SCROLL', 'LIKE', 'COMMENT', 'SHARE']))
            elif self.app_name == 'web-browser':
                interactions.append(random.choice(['CLICK', 'SCROLL', 'NEW_TAB', 'SEARCH']))
        
        return interactions
    
    def calculate_bandwidth_usage(self):
        """Calcule l'utilisation de bande passante"""
        base_bandwidth = self.config.get('bandwidth_mbps', 1.0)
        # Variation aléatoire de ±20%
        variation = random.uniform(0.8, 1.2)
        current_bandwidth = base_bandwidth * variation
        
        # Conversion en MB pour les métriques
        data_mb = current_bandwidth / 8  # Mbps to MB/s
        return current_bandwidth, data_mb
    
    def run(self):
        """Boucle principale de simulation"""
        self.running = True
        self.metrics['start_time'] = datetime.now()
        
        print(f"[{datetime.now()}] Starting {self.app_name} infotainment application")
        print(f"[{datetime.now()}] Priority: {self.config.get('priority', 'unknown')}")
        print(f"[{datetime.now()}] Expected bandwidth: {self.config.get('bandwidth_mbps', 0)}Mbps")
        
        update_interval = self.config.get('update_interval_ms', 1000) / 1000.0
        
        while self.running:
            cycle_start = time.time()
            
            # Simulation du traitement de contenu
            content_info = self.simulate_content_processing()
            
            # Calcul utilisation bande passante
            bandwidth_mbps, data_mb = self.calculate_bandwidth_usage()
            self.metrics['data_processed_mb'] += data_mb * update_interval
            
            # Traitement des interactions utilisateur
            interactions = self.process_user_interactions()
            
            if interactions:
                self.metrics['user_interactions'] += len(interactions)
                for interaction in interactions:
                    print(f"[{datetime.now()}] {self.app_name}: {interaction}")
            
            # Simulation de nouveau contenu
            if random.random() < 0.02:  # 2% chance de nouveau contenu
                self.metrics['content_played'] += 1
                content_type = random.choice(self.config.get('content_types', ['content']))
                print(f"[{datetime.now()}] {self.app_name}: 🎵 NEW_CONTENT_STARTED ({content_type})")
            
            # Affichage statut normal périodique
            if self.metrics['cycles'] % 20 == 0:  # Toutes les 20 cycles
                uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
                print(f"[{datetime.now()}] {self.app_name}: Streaming normally - "
                      f"Cycle {self.metrics['cycles']}, Uptime: {uptime:.1f}s, "
                      f"Bandwidth: {bandwidth_mbps:.1f}Mbps, "
                      f"Data: {self.metrics['data_processed_mb']:.1f}MB, "
                      f"Interactions: {self.metrics['user_interactions']}")
            
            self.metrics['cycles'] += 1
            
            # Respecter l'intervalle de mise à jour
            cycle_time = time.time() - cycle_start
            sleep_time = max(0, update_interval - cycle_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

if __name__ == '__main__':
    app_name = os.environ.get('APP_NAME', 'media-player')
    
    print("🎬 SDV Infotainment Application Simulator")
    print("="*50)
    print(f"Application: {app_name}")
    print(f"Priority: {os.environ.get('SDV_PRIORITY', 'low')}")
    print(f"Real-time mode: {os.environ.get('SDV_REAL_TIME', 'false')}")
    print(f"Pod: {os.environ.get('HOSTNAME', 'unknown')}")
    print("="*50)
    
    simulator = InfotainmentAppSimulator(app_name)
    
    try:
        simulator.run()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] {app_name} shutting down...")
        uptime = (datetime.now() - simulator.metrics['start_time']).total_seconds()
        print(f"[{datetime.now()}] Final metrics:")
        print(f"  • Uptime: {uptime:.1f}s")
        print(f"  • Cycles: {simulator.metrics['cycles']}")
        print(f"  • Content played: {simulator.metrics['content_played']}")
        print(f"  • User interactions: {simulator.metrics['user_interactions']}")
        print(f"  • Data processed: {simulator.metrics['data_processed_mb']:.1f}MB")
        simulator.running = False 