# AXIL SDV Testbench 

- `axil_complete.py` : **Orchestrateur principal**. Gère les états du véhicule, surveille les ressources et déploie les applications sur le cluster Kubernetes.
- `resource_monitor.py` : **Moniteur de ressources**. Vérifie l'utilisation CPU, mémoire, réseau (limite 10 Mbps) et disque des nœuds.
- `vehicle_simulator.py` : **Simulateur d'états**. Génère des transitions réalistes entre les états du véhicule (conduite, stationnement, charge, urgence).
- `axil_orchestrator.py` : Version simplifiée de l'orchestrateur (non utilisée dans l'implémentation principale, pour référence).