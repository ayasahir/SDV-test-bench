#!/usr/bin/env python3
"""
AXIL Orchestrator - SDV Testbench (Multi-mode + Profils)
- États véhicule: driving / parking / charging / emergency
- 2 modes par application (mode 1 = performance, mode 2 = éco)
- Profils UX via user_profiles.yaml (sinon poids par défaut)
- Baseline optionnelle (--baseline): sélection naïve des modes 1
- Limite réseau TAS: 10 Mbps (globale)
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
import os
import sys
import argparse

# =================== CONFIG ===================

DEFAULT_WEIGHTS = {"safety": 3.0, "comfort": 2.0, "infotainment": 1.0}
PROFILES_FILE = "user_profiles.yaml"
NETWORK_BW_LIMIT_Mbps = 10.0  # TAS best-effort 10 Mbps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/axil.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# =================== ÉTATS VÉHICULE ===================

class VehicleStateManager:
    def __init__(self, interval_s: int = 10):
        self.states = ["driving", "parking", "charging", "emergency"]
        self.current_state = "parking"
        self.state_change_interval = interval_s
        self.running = True

    def get_current_state(self):
        return self.current_state

    def change_state_randomly(self):
        old = self.current_state
        self.current_state = random.choice(self.states)
        if old != self.current_state:
            logger.info(f"État véhicule changé: {old} → {self.current_state}")
        return self.current_state

    def start_state_monitor(self):
        def loop():
            while self.running:
                time.sleep(self.state_change_interval)
                if self.running:
                    self.change_state_randomly()
        threading.Thread(target=loop, daemon=True).start()
        logger.info(f"Monitoring d'état (changement toutes les {self.state_change_interval}s)")

# =================== RESSOURCES ===================

class ResourceMonitor:
    def get_node_resources(self, node_name):
        # Simulation; à remplacer par metrics-server/metrics.k8s.io si dispo
        cpu_percent = random.uniform(20, 80)
        mem_percent = random.uniform(30, 70)
        return {
            "cpu_available": 100 - cpu_percent,
            "memory_available": 100 - mem_percent,
            "network_bandwidth": random.uniform(5, 10),  # Mbps disponible
        }

    def check_resource_constraints(self, node_name, req):
        r = self.get_node_resources(node_name)
        ok = (
            r["cpu_available"] >= req.get("cpu", 10)
            and r["memory_available"] >= req.get("memory", 10)
            and r["network_bandwidth"] >= req.get("bandwidth", 1)
        )
        return ok, r

# =================== APPS (avec modes) ===================

class ApplicationManager:
    """
    On reprend tes apps, mais on leur attribue 2 modes:
      - mode 1 (perf): cpu×2, mem×2, bw×1.5, ux=2.0
      - mode 2 (éco) : cpu×1, mem×1, bw×1.0, ux=1.0
    Les unités restent cohérentes avec ton script initial:
      - cpu: "m" (on garde tes petits nombres en simulation)
      - memory: "Mi"
      - bandwidth: Mbps
    """

    def __init__(self):
        self.apps_config = self._load_apps_configuration()

    def _base_apps(self):
        safety = [
            {"name": "emergency-brake", "priority": 1, "cpu": 15, "memory": 20, "bandwidth": 2.0, "category": "safety"},
            {"name": "collision-avoidance", "priority": 1, "cpu": 20, "memory": 25, "bandwidth": 3.0, "category": "safety"},
            {"name": "lane-keeping", "priority": 2, "cpu": 12, "memory": 15, "bandwidth": 1.5, "category": "safety"},
            {"name": "adaptive-cruise", "priority": 2, "cpu": 18, "memory": 22, "bandwidth": 2.5, "category": "safety"},
            {"name": "driver-monitoring", "priority": 1, "cpu": 10, "memory": 18, "bandwidth": 1.0, "category": "safety"},
            {"name": "traffic-sign-detection", "priority": 2, "cpu": 25, "memory": 30, "bandwidth": 2.0, "category": "safety"},
            {"name": "pedestrian-detection", "priority": 1, "cpu": 22, "memory": 28, "bandwidth": 2.5, "category": "safety"},
            {"name": "vehicle-tracking", "priority": 2, "cpu": 16, "memory": 20, "bandwidth": 1.8, "category": "safety"},
            {"name": "emergency-call", "priority": 1, "cpu": 5,  "memory": 10, "bandwidth": 0.5, "category": "safety"},
            {"name": "airbag-control", "priority": 1, "cpu": 8,  "memory": 12, "bandwidth": 0.3, "category": "safety"},
        ]
        comfort = [
            {"name": "climate-control", "priority": 3, "cpu": 8, "memory": 12, "bandwidth": 0.5, "category": "comfort"},
            {"name": "seat-adjustment", "priority": 4, "cpu": 5, "memory": 8,  "bandwidth": 0.2, "category": "comfort"},
            {"name": "lighting-control", "priority": 3, "cpu": 6, "memory": 10, "bandwidth": 0.3, "category": "comfort"},
            {"name": "mirror-adjustment", "priority": 4, "cpu": 4, "memory": 6,  "bandwidth": 0.2, "category": "comfort"},
            {"name": "parking-assist", "priority": 3, "cpu": 15,"memory": 20, "bandwidth": 1.5, "category": "comfort"},
            {"name": "navigation-basic", "priority": 3, "cpu": 12,"memory": 18, "bandwidth": 1.0, "category": "comfort"},
            {"name": "voice-commands", "priority": 3, "cpu": 10,"memory": 15, "bandwidth": 0.8, "category": "comfort"},
            {"name": "gesture-control", "priority": 4, "cpu": 14,"memory": 16, "bandwidth": 0.6, "category": "comfort"},
            {"name": "ambient-lighting", "priority": 4, "cpu": 3, "memory": 5,  "bandwidth": 0.1, "category": "comfort"},
            {"name": "massage-seats", "priority": 4, "cpu": 6, "memory": 8,  "bandwidth": 0.2, "category": "comfort"},
        ]
        infot = [
            {"name": "media-player", "priority": 5, "cpu": 15,"memory": 25, "bandwidth": 2.0, "category": "infotainment"},
            {"name": "streaming-video", "priority": 5, "cpu": 25,"memory": 40, "bandwidth": 5.0, "category": "infotainment"},
            {"name": "games-engine", "priority": 5, "cpu": 30,"memory": 50, "bandwidth": 3.0, "category": "infotainment"},
            {"name": "social-media", "priority": 5, "cpu": 12,"memory": 20, "bandwidth": 2.5, "category": "infotainment"},
            {"name": "web-browser", "priority": 5, "cpu": 20,"memory": 35, "bandwidth": 3.5, "category": "infotainment"},
            {"name": "music-streaming","priority": 4, "cpu": 8, "memory": 15, "bandwidth": 1.5, "category": "infotainment"},
            {"name": "video-calls", "priority": 4, "cpu": 18,"memory": 28, "bandwidth": 4.0, "category": "infotainment"},
            {"name": "ar-navigation","priority": 4, "cpu": 35,"memory": 45, "bandwidth": 4.5, "category": "infotainment"},
            {"name": "news-reader", "priority": 5, "cpu": 6, "memory": 12, "bandwidth": 1.0, "category": "infotainment"},
            {"name": "weather-app", "priority": 5, "cpu": 4, "memory": 8,  "bandwidth": 0.5, "category": "infotainment"},
        ]
        return safety + comfort + infot

    def _make_modes(self, base):
        # Mode 1 (perf) et Mode 2 (éco)
        return [
            {
                "mode_id": 1,
                "cpu": int(base["cpu"] * 2),
                "memory": int(base["memory"] * 2),
                "bandwidth": base["bandwidth"] * 1.5,
                "ux_value": 2.0,  # meilleur UX
            },
            {
                "mode_id": 2,
                "cpu": int(base["cpu"]),
                "memory": int(base["memory"]),
                "bandwidth": base["bandwidth"] * 1.0,
                "ux_value": 1.0,  # UX standard
            },
        ]

    def _load_apps_configuration(self):
        apps = []
        for base in self._base_apps():
            base = dict(base)  # copy
            base["modes"] = self._make_modes(base)
            apps.append(base)
        logger.info(f"Configuration chargée: {len(apps)} applications (multimode)")
        return apps

    def get_apps_for_state(self, vehicle_state):
        # mapping d’origine étendu
        return {
            "driving": {
                "safety": [
                    "emergency-brake", "collision-avoidance", "lane-keeping",
                    "adaptive-cruise", "driver-monitoring", "traffic-sign-detection",
                    "pedestrian-detection", "vehicle-tracking",
                ],
                "comfort": ["climate-control", "navigation-basic", "voice-commands"],
                "infotainment": ["music-streaming"],
            },
            "parking": {
                "safety": ["emergency-brake", "driver-monitoring", "emergency-call"],
                "comfort": [
                    "climate-control", "seat-adjustment", "lighting-control",
                    "mirror-adjustment", "parking-assist",
                ],
                "infotainment": ["media-player", "social-media", "web-browser", "news-reader"],
            },
            "charging": {
                "safety": ["emergency-call", "airbag-control"],
                "comfort": ["climate-control", "seat-adjustment", "ambient-lighting", "massage-seats"],
                "infotainment": ["streaming-video", "games-engine", "video-calls", "ar-navigation", "weather-app"],
            },
            "emergency": {
                "safety": ["emergency-brake", "collision-avoidance", "driver-monitoring", "emergency-call", "airbag-control"],
                "comfort": [],
                "infotainment": [],
            },
        }.get(vehicle_state, {"safety": [], "comfort": [], "infotainment": []})

# =================== ORCHESTRATEUR ===================

class AXILOrchestrator:
    def __init__(self, profile_name=None, baseline=False):
        self.vehicle_state_manager = VehicleStateManager()
        self.resource_monitor = ResourceMonitor()
        self.app_manager = ApplicationManager()
        self.metrics = {"deployments": 0, "failures": 0, "optimization_time": [], "network_health": [], "resource_usage": []}
        self.baseline = baseline
        self.profile_weights = self._load_user_profile(profile_name)

        try:
            config.load_kube_config()
            self.k8s_apps = client.AppsV1Api()
            self.k8s_core = client.CoreV1Api()
            logger.info("Connexion Kubernetes établie")
        except Exception as e:
            logger.error(f"Erreur connexion Kubernetes: {e}")
            sys.exit(1)

    def _app_score(self, app):
        # Score AXIL strict: priorité × poids(catégorie)
        return app["priority"] * self.profile_weights.get(app["category"], 1.0)


    def _load_user_profile(self, profile_name):
        if not profile_name:
            logger.info("Profil UX: défaut (poids globaux)")
            return DEFAULT_WEIGHTS
        if not os.path.exists(PROFILES_FILE):
            logger.warning("user_profiles.yaml introuvable → poids par défaut")
            return DEFAULT_WEIGHTS
        try:
            with open(PROFILES_FILE, "r") as f:
                profiles = yaml.safe_load(f) or {}
            weights = profiles.get(profile_name, DEFAULT_WEIGHTS)
            logger.info(f"Profil UX chargé: {profile_name} -> {weights}")
            return weights
        except Exception as e:
            logger.error(f"Erreur lecture profils: {e}")
            return DEFAULT_WEIGHTS

    def _score_mode(self, app, mode):
        # Score = priorité × poids(catégorie) × ux_mode
        w = self.profile_weights.get(app["category"], 1.0)
        return app["priority"] * w * mode["ux_value"]

    def optimize_deployments(self):
        t0 = time.time()
        state = self.vehicle_state_manager.get_current_state()
        required = self.app_manager.get_apps_for_state(state)

        logger.info(f"Optimisation pour état: {state}")

        # 1) Construire la liste unique des apps requises (pas par mode)
        required_names = set()
        for names in required.values():
            required_names.update(names)

        required_apps = []
        for name in required_names:
            app = next((a for a in self.app_manager.apps_config if a["name"] == name), None)
            if app:
                required_apps.append(app)

        # 2) Trier les apps par score AXIL = priority × weight (décroissant)
        required_apps.sort(key=lambda a: self._app_score(a), reverse=True)

        plan = {}
        total_bw = 0.0
        picked_apps = set()

        # 3) Pour chaque app (dans l'ordre AXIL), tenter le meilleur mode d'abord (1), sinon retrograder au mode 2
        for app in required_apps:
            if app["name"] in picked_apps:
                continue

            zone = f"node-{app['category']}"  # mapping simple: zone=catégorie
            modes_by_id = {m["mode_id"]: m for m in app["modes"]}

            # Ordre d’essai des modes
            try_order = [1, 2] if not self.baseline else [1]  # baseline: que mode 1

            deployed = False
            for mid in try_order:
                if mid not in modes_by_id:
                    continue
                mode = modes_by_id[mid]

                # Limite réseau TAS globale
                if total_bw + mode["bandwidth"] > NETWORK_BW_LIMIT_Mbps:
                    continue

                # Contraintes de ressources nœud
                req = {"cpu": mode["cpu"], "memory": mode["memory"], "bandwidth": mode["bandwidth"]}
                ok, res = self.resource_monitor.check_resource_constraints(zone, req)
                if not ok:
                    continue

                # OK → planifier
                plan.setdefault(zone, []).append({"app": app, "mode": mode})
                picked_apps.add(app["name"])
                total_bw += mode["bandwidth"]
                logger.info(f"✓ {app['name']} sélectionnée (mode {mid}) sur {zone} | score={self._app_score(app):.2f}")
                deployed = True
                break

            if not deployed:
                logger.warning(f"⚠️  {app['name']} rejetée (aucun mode ne respecte contraintes/TAS)")

        opt_time = time.time() - t0
        self.metrics["optimization_time"].append(opt_time)
        logger.info(f"Temps d'optimisation: {opt_time:.2f}s | Utilisation réseau: {total_bw:.2f}/{NETWORK_BW_LIMIT_Mbps} Mbps")
        return plan, total_bw

        

    def _deploy_single(self, app, mode, zone):
        app_name = app["name"]
        # Construire le Deployment avec ressources dépendantes du mode
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=f"sdv-{app_name}",
                namespace="default",
                labels={"app": app_name, "zone": zone, "category": app["category"], "priority": str(app["priority"]), "mode": str(mode["mode_id"])},
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": app_name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": app_name, "zone": zone, "mode": str(mode["mode_id"])}),
                    spec=client.V1PodSpec(
                        node_selector={"zone": zone},
                        containers=[
                            client.V1Container(
                                name=app_name,
                                image="busybox:latest",
                                command=["sh", "-c"],
                                args=[f"while true; do echo '[{datetime.now()}] {app_name} (mode {mode['mode_id']}) running on {zone}'; sleep 5; done"],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": f"{mode['cpu']}m", "memory": f"{mode['memory']}Mi"},
                                    limits={"cpu": f"{mode['cpu']*2}m", "memory": f"{mode['memory']*2}Mi"},
                                ),
                            )
                        ],
                    ),
                ),
            ),
        )
        try:
            # Supprimer ancien déploiement (si présent)
            try:
                self.k8s_apps.delete_namespaced_deployment(name=f"sdv-{app_name}", namespace="default")
                time.sleep(1)
            except ApiException:
                pass
            # Créer
            self.k8s_apps.create_namespaced_deployment(namespace="default", body=deployment)
            logger.debug(f"{app_name} déployé (mode {mode['mode_id']}) sur {zone}")
            return True
        except ApiException as e:
            logger.error(f"Erreur K8s pour {app_name}: {e}")
            return False

    def deploy_applications(self, plan):
        deployed = 0
        for zone, items in plan.items():
            for entry in items:
                if self._deploy_single(entry["app"], entry["mode"], zone):
                    deployed += 1
                    self.metrics["deployments"] += 1
                else:
                    self.metrics["failures"] += 1
        logger.info(f"Applications déployées: {deployed}")
        return deployed

    def collect_metrics(self):
        try:
            network_health = random.uniform(75, 95)
            self.metrics["network_health"].append(network_health)

            pods = self.k8s_core.list_pod_for_all_namespaces()
            running = len([p for p in pods.items if p.status.phase == "Running" and p.metadata.name.startswith("sdv-")])
            resource_usage = min(100, (running / 30) * 100)
            self.metrics["resource_usage"].append(resource_usage)

            logger.info(f"Métriques - Réseau: {network_health:.1f}% | Ressources: {resource_usage:.1f}%")
        except Exception as e:
            logger.error(f"Erreur collecte métriques: {e}")

    def cleanup_unused_apps(self):
        try:
            deployments = self.k8s_apps.list_namespaced_deployment(namespace="default")
            state = self.vehicle_state_manager.get_current_state()
            required = self.app_manager.get_apps_for_state(state)
            required_names = set(sum(required.values(), []))
            cleaned = 0
            for d in deployments.items:
                if d.metadata.name.startswith("sdv-"):
                    app_name = d.metadata.name[4:]
                    if app_name not in required_names:
                        self.k8s_apps.delete_namespaced_deployment(name=d.metadata.name, namespace="default")
                        cleaned += 1
                        logger.info(f"App {app_name} supprimée (non requise)")
            if cleaned:
                logger.info(f"{cleaned} applications nettoyées")
        except Exception as e:
            logger.error(f"Erreur nettoyage: {e}")

    def print_status(self):
        state = self.vehicle_state_manager.get_current_state()
        try:
            pods = self.k8s_core.list_pod_for_all_namespaces()
            running = len([p for p in pods.items if p.status.phase == "Running" and p.metadata.name.startswith("sdv-")])
            avg_opt = (sum(self.metrics["optimization_time"][-5:]) / max(1, min(5, len(self.metrics["optimization_time"])))) if self.metrics["optimization_time"] else 0
            print("\n" + "=" * 60)
            print(f" État véhicule: {state.upper()}")
            print(f" Applications actives: {running}/30")
            print(f" Temps optimisation moyen: {avg_opt:.2f}s")
            print(f" Déploiements réussis: {self.metrics['deployments']}")
            print(f" Échecs: {self.metrics['failures']}")
            if self.metrics["network_health"]:
                print(f" Santé réseau: {self.metrics['network_health'][-1]:.1f}%")
            print("=" * 60 + "\n")
        except Exception as e:
            logger.error(f"Erreur affichage statut: {e}")

    def run(self, duration_s=60):
        logger.info("AXIL Orchestrator (multimode) démarré")
        self.vehicle_state_manager.start_state_monitor()
        t0 = time.time()
        cycles = 0
        try:
            while time.time() - t0 < duration_s:
                cycles += 1
                logger.info(f"\n=== CYCLE {cycles} ===")
                plan, net_used = self.optimize_deployments()
                self.deploy_applications(plan)
                self.cleanup_unused_apps()
                self.collect_metrics()
                self.print_status()
                time.sleep(8)
        except KeyboardInterrupt:
            logger.info("Arrêt demandé par l'utilisateur")
        finally:
            self.vehicle_state_manager.running = False
            total_time = time.time() - t0
            logger.info("\n=== RAPPORT FINAL SDV TESTBENCH ===")
            logger.info(f"Durée totale: {total_time:.1f}s | Cycles exécutés: {cycles}")
            logger.info(f"Déploiements totaux: {self.metrics['deployments']} | Échecs: {self.metrics['failures']}")
            if self.metrics["optimization_time"]:
                logger.info(f"Temps optimisation moyen: {sum(self.metrics['optimization_time'])/len(self.metrics['optimization_time']):.2f}s")
            if self.metrics["network_health"]:
                avg_net = sum(self.metrics["network_health"]) / len(self.metrics["network_health"])
                logger.info(f"Santé réseau moyenne: {avg_net:.1f}%")
            logger.info("Test SDV terminé")

# =================== MAIN ===================

if __name__ == "__main__":
    print("AXIL Orchestrator (multimode) – SDV Testbench")
    print("Ctrl+C pour arrêter\n")

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=str, help="Nom du profil utilisateur (ex: gaming, eco)")
    parser.add_argument("--baseline", action="store_true", help="Activer le mode baseline (naïf, modes 1 seulement)")
    parser.add_argument("--duration", type=int, default=60, help="Durée du test (secondes)")
    args = parser.parse_args()

    orch = AXILOrchestrator(profile_name=args.profile, baseline=args.baseline)
    orch.run(duration_s=args.duration)
