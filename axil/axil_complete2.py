import os
import time
import csv
import random
import yaml
from kubernetes import client, config

DEFAULT_WEIGHTS = {
    "safety": 3.0,
    "comfort": 2.0,
    "infotainment": 1.0
}

VEHICLE_STATES = ["urban", "highway", "idle"]
STATE_CATEGORIES = {
    "urban": ["safety", "comfort"],
    "highway": ["safety", "infotainment"],
    "idle": ["comfort", "infotainment"]
}

NETWORK_BW_LIMIT = 10000
METRICS_FILE = "metrics.csv"
TRACE_FILE = "app_trace.csv"
PROFILES_FILE = "user_profiles.yaml"

class VehicleStateManager:
    def __init__(self):
        self.states = VEHICLE_STATES
        self.index = 0

    def get_current_state(self):
        return self.states[self.index]

    def update_state(self):
        self.index = (self.index + 1) % len(self.states)

    def get_active_categories(self):
        return STATE_CATEGORIES[self.get_current_state()]

class AXILOrchestrator:
    def __init__(self, profile_name=None, baseline=False):
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.app_configs = []
        self.vehicle_state = VehicleStateManager()
        self.profile_weights = self.load_user_profile(profile_name)
        self.load_static_configs()
        self.init_metrics_files()
        self.cycle_count = 0
        self.baseline = baseline

    def load_user_profile(self, profile_name):
        if profile_name is None:
            return DEFAULT_WEIGHTS
        if not os.path.exists(PROFILES_FILE):
            print("[AXIL] Warning: user_profiles.yaml not found. Using default weights.")
            return DEFAULT_WEIGHTS
        with open(PROFILES_FILE, 'r') as f:
            profiles = yaml.safe_load(f)
        return profiles.get(profile_name, DEFAULT_WEIGHTS)

    def load_static_configs(self):
        self.app_configs = [
                    # --- SAFETY ---
                    {"app_name": "emergency_brake", "category": "safety", "priority": 10,
                    "modes": [{"mode_id": 1, "cpu": 400, "memory": 256, "bandwidth": 3000, "ux_value": 10},
                            {"mode_id": 2, "cpu": 200, "memory": 128, "bandwidth": 1500, "ux_value": 6}]},
                    
                    {"app_name": "collision_warning", "category": "safety", "priority": 9,
                    "modes": [{"mode_id": 1, "cpu": 300, "memory": 256, "bandwidth": 2500, "ux_value": 9},
                            {"mode_id": 2, "cpu": 150, "memory": 128, "bandwidth": 1300, "ux_value": 5}]},

                    {"app_name": "lane_assist", "category": "safety", "priority": 8,
                    "modes": [{"mode_id": 1, "cpu": 250, "memory": 200, "bandwidth": 2000, "ux_value": 8},
                            {"mode_id": 2, "cpu": 125, "memory": 100, "bandwidth": 1000, "ux_value": 4}]},

                    # --- COMFORT ---
                    {"app_name": "climate_control", "category": "comfort", "priority": 6,
                    "modes": [{"mode_id": 1, "cpu": 300, "memory": 200, "bandwidth": 2000, "ux_value": 6},
                            {"mode_id": 2, "cpu": 150, "memory": 100, "bandwidth": 1000, "ux_value": 3}]},

                    {"app_name": "seat_massage", "category": "comfort", "priority": 5,
                    "modes": [{"mode_id": 1, "cpu": 200, "memory": 150, "bandwidth": 1200, "ux_value": 5},
                            {"mode_id": 2, "cpu": 100, "memory": 75, "bandwidth": 600, "ux_value": 2}]},

                    {"app_name": "cabin_lighting", "category": "comfort", "priority": 3,
                    "modes": [{"mode_id": 1, "cpu": 100, "memory": 64, "bandwidth": 500, "ux_value": 2},
                            {"mode_id": 2, "cpu": 50, "memory": 32, "bandwidth": 250, "ux_value": 1}]},

                    # --- INFOTAINMENT ---
                    {"app_name": "music_player", "category": "infotainment", "priority": 4,
                    "modes": [{"mode_id": 1, "cpu": 200, "memory": 128, "bandwidth": 1500, "ux_value": 4},
                            {"mode_id": 2, "cpu": 100, "memory": 64, "bandwidth": 800, "ux_value": 2}]},

                    {"app_name": "video_streaming", "category": "infotainment", "priority": 7,
                    "modes": [{"mode_id": 1, "cpu": 300, "memory": 256, "bandwidth": 3000, "ux_value": 7},
                            {"mode_id": 2, "cpu": 150, "memory": 128, "bandwidth": 1500, "ux_value": 3}]},

                    {"app_name": "navigation_display", "category": "infotainment", "priority": 6,
                    "modes": [{"mode_id": 1, "cpu": 250, "memory": 192, "bandwidth": 2200, "ux_value": 6},
                            {"mode_id": 2, "cpu": 125, "memory": 96, "bandwidth": 1100, "ux_value": 3}]}
                ]


    def init_metrics_files(self):
        if not os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "vehicle_state", "apps_deployed", "failed_apps", "total_cpu", "total_mem", "total_bw", "global_ux", "mode"])
        if not os.path.exists(TRACE_FILE):
            with open(TRACE_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["cycle", "vehicle_state", "app_name", "category", "global_ux_value", "deployed", "reason", "mode"])

    def optimize(self, active_categories):
        selected_modes = []
        total_bw = 0
        total_cpu = 0
        total_mem = 0
        global_ux = 0
        trace_logs = []

        if self.baseline:
            # Baseline = naïf, on prend les modes 1 seulement, triés par priorité
            all_apps = [app for app in self.app_configs if app["category"] in active_categories]
            all_apps.sort(key=lambda a: a["priority"], reverse=True)
            for app in all_apps:
                mode = app["modes"][0]  # mode 1 uniquement
                if total_bw + mode["bandwidth"] <= NETWORK_BW_LIMIT:
                    selected_modes.append({
                        **mode,
                        "app_name": app["app_name"],
                        "category": app["category"],
                        "priority": app["priority"],
                        "global_ux": 0  # non utilisé ici
                    })
                    total_bw += mode["bandwidth"]
                    total_cpu += mode["cpu"]
                    total_mem += mode["memory"]
                    trace_logs.append([self.cycle_count, self.vehicle_state.get_current_state(), app["app_name"], app["category"], 0, 1, "selected", "baseline"])
                else:
                    trace_logs.append([self.cycle_count, self.vehicle_state.get_current_state(), app["app_name"], app["category"], 0, 0, "bandwidth_limit", "baseline"])
            return selected_modes, total_cpu, total_mem, total_bw, 0, trace_logs

        # AXIL mode : UX-aware + rétrogradation
        all_apps = [app for app in self.app_configs if app["category"] in active_categories]
        scored_modes = []
        for app in all_apps:
            weight = self.profile_weights.get(app["category"], 1.0)
            for mode in app["modes"]:
                scored_modes.append({
                    **mode,
                    "app_name": app["app_name"],
                    "category": app["category"],
                    "priority": app["priority"],
                    "global_ux": app["priority"] * weight * mode["ux_value"]
                })

        # Tri par score décroissant
        scored_modes.sort(key=lambda m: m["global_ux"], reverse=True)

        deployed_apps = set()
        for mode in scored_modes:
            app_name = mode["app_name"]
            if app_name in deployed_apps:
                continue  # éviter doublons si on a déjà déployé cette app dans un mode

            if total_bw + mode["bandwidth"] <= NETWORK_BW_LIMIT:
                selected_modes.append(mode)
                deployed_apps.add(app_name)
                total_bw += mode["bandwidth"]
                total_cpu += mode["cpu"]
                total_mem += mode["memory"]
                global_ux += mode["global_ux"]
                trace_logs.append([self.cycle_count, self.vehicle_state.get_current_state(), app_name, mode["category"], mode["global_ux"], 1, f"selected_mode_{mode['mode_id']}", "AXIL"])
            else:
                # essayer le mode inférieur s'il existe
                app_modes = [m for m in self.app_configs if m["app_name"] == app_name][0]["modes"]
                current_mode_id = mode["mode_id"]
                lower_modes = [m for m in app_modes if m["mode_id"] > current_mode_id]

                downgraded = False
                for m in lower_modes:
                    # recalculer le global_ux pour le mode inférieur
                    weight = self.profile_weights.get(mode["category"], 1.0)
                    new_ux = mode["priority"] * weight * m["ux_value"]
                    if total_bw + m["bandwidth"] <= NETWORK_BW_LIMIT:
                        selected_modes.append({
                            **m,
                            "app_name": app_name,
                            "category": mode["category"],
                            "priority": mode["priority"],
                            "global_ux": new_ux
                        })
                        deployed_apps.add(app_name)
                        total_bw += m["bandwidth"]
                        total_cpu += m["cpu"]
                        total_mem += m["memory"]
                        global_ux += new_ux
                        trace_logs.append([self.cycle_count, self.vehicle_state.get_current_state(), app_name, mode["category"], new_ux, 1, f"downgraded_to_mode_{m['mode_id']}", "AXIL"])
                        downgraded = True
                        break

                if not downgraded:
                    trace_logs.append([self.cycle_count, self.vehicle_state.get_current_state(), app_name, mode["category"], mode["global_ux"], 0, "rejected_all_modes", "AXIL"])

        return selected_modes, total_cpu, total_mem, total_bw, global_ux, trace_logs


    def deploy_selected_apps(self, selected_modes):
        print("\n[Orchestrator] Deploying selected applications:")
        for mode in selected_modes:
            print(f"- {mode['app_name']} (mode {mode['mode_id']})")

    def log_metrics(self, state, selected_modes, cpu, mem, bw, ux, trace_logs):
        with open(METRICS_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([int(time.time()), state, len(selected_modes), len(trace_logs) - len(selected_modes), cpu, mem, bw, ux, "AXIL" if not self.baseline else "baseline"])

        with open(TRACE_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(trace_logs)

    def run(self):
        while True:
            state = self.vehicle_state.get_current_state()
            categories = self.vehicle_state.get_active_categories()

            print(f"\n[Orchestrator] Vehicle state: {state.upper()}  | Mode: {'AXIL' if not self.baseline else 'BASELINE'}")
            selected_modes, cpu, mem, bw, ux, trace_logs = self.optimize(categories)
            self.deploy_selected_apps(selected_modes)
            self.log_metrics(state, selected_modes, cpu, mem, bw, ux, trace_logs)

            self.cycle_count += 1
            if self.cycle_count % 3 == 0:
                self.vehicle_state.update_state()
            time.sleep(8)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=str, help="Nom du profil utilisateur (ex: gaming, eco)")
    parser.add_argument("--baseline", action="store_true", help="Activer le mode baseline (naïf)")
    args = parser.parse_args()

    orchestrator = AXILOrchestrator(profile_name=args.profile, baseline=args.baseline)
    orchestrator.run()
