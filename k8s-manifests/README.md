## Fichiers et leurs rôles

### 1. `safety-app.yaml`
- **Rôle** : Configure les déploiements des applications critiques pour la sécurité du véhicule.
- **Applications incluses** :
  - **emergency-brake** : Active le freinage d'urgence (priorité 1).
  - **collision-avoidance** : Évite les collisions (priorité 1).
  - **lane-keeping** : Maintient le véhicule dans sa voie (priorité 2).
  - **adaptive-cruise** : Régule la vitesse adaptative (priorité 2).
  - **driver-monitoring** : Surveille l'état du conducteur (priorité 1).
- **Caractéristiques** :
  - Toutes les applications sont déployées dans la zone `safety` avec un sélecteur de nœud (`nodeSelector: zone: safety`).
  - Utilisent l'image Docker `sdv-testbench/sdv-safety:latest`.
  - Définissent des ressources (CPU, mémoire) et des limites de bande passante.
  - Priorités élevées (1 ou 2) pour garantir une exécution rapide.

### 2. `comfort-app.yaml`
- **Rôle** : Configure les applications liées au confort des passagers.
- **Applications incluses** :
  - **climate-control** : Contrôle la climatisation (priorité 3).
  - **seat-adjustment** : Ajuste les sièges (priorité 4).
  - **lighting-control** : Gère l'éclairage intérieur (priorité 3).
  - **parking-assist** : Aide au stationnement (priorité 3).
  - **navigation-basic** : Fournit une navigation de base (priorité 3).
- **Caractéristiques** :
  - Déployées dans la zone `comfort` (`nodeSelector: zone: comfort`).
  - Utilisent l'image `sdv-testbench/sdv-comfort:latest`.
  - Priorités moyennes (3 ou 4) pour un traitement moins critique que les applications de sécurité.
  - Consomment moins de ressources que les applications de sécurité.

### 3. `infotainment-app.yaml`
- **Rôle** : Configure les applications de divertissement pour les passagers.
- **Applications incluses** :
  - **media-player** : Lecteur multimédia (priorité 5).
  - **streaming-video** : Streaming vidéo (priorité 5).
  - **games-engine** : Moteur de jeux (priorité 5).
  - **social-media** : Gestion des réseaux sociaux (priorité 5).
  - **web-browser** : Navigation internet (priorité 5).
  - **music-streaming** : Streaming musical (priorité 4).
- **Caractéristiques** :
  - Déployées dans la zone `infotainment` (`nodeSelector: zone: infotainment`).
  - Utilisent principalement l'image `sdv-testbench/sdv-infotainment:latest` (sauf `games-engine`, `social-media`, et `web-browser` qui utilisent `busybox:latest` pour des simulations simples).
  - Priorités basses (4 ou 5) car non critiques pour la sécurité.
  - Consomment plus de ressources (surtout pour le streaming vidéo et les jeux).

## Orchestration par Kubernetes :
  - Chaque fichier YAML définit des déploiements (`kind: Deployment`) qui sont appliqués au cluster Kubernetes via la commande `kubectl apply -f <fichier>.yaml`.
  - Les déploiements sont assignés à des nœuds spécifiques (Raspberry Pi) grâce au `nodeSelector` basé sur la zone (`safety`, `comfort`, `infotainment`).
  - Le nœud maître (orchestrateur) gère la distribution des applications aux nœuds travailleurs, chacun dédié à une zone spécifique.

## Zonage et priorisation :
  - Les applications sont regroupées par zone pour simuler une séparation physique des fonctions dans un véhicule (sécurité, confort, divertissement).
  - Les priorités (de 1 à 5) permettent à l'orchestrateur de prioriser les applications critiques (ex. `emergency-brake`) sur les moins critiques (ex. `games-engine`).

## Gestion des ressources :
  - Chaque déploiement spécifie des requêtes et limites de ressources (CPU, mémoire) pour éviter la surcharge des Raspberry Pi.
  - La bande passante (`BANDWIDTH_LIMIT`) est définie pour respecter les contraintes réseau (limite TSN/TAS de 10 Mbps).

## Instructions pour l'utilisation

1. **Préparer le cluster** :
   - Exécutez `run_baseline_local.sh` pour créer un cluster K3d et déployer les applications des fichiers YAML :
     ```bash
     ./run_baseline_local.sh
     ```

2. **Lancer l'orchestrateur** :
   - Exécutez `axil_complete.py` pour orchestrer dynamiquement les applications en fonction des états du véhicule :
     ```bash
     python3 axil_complete.py
     ```

3. **Surveiller les ressources** :
   - Lancez `resource_monitor.py` pour vérifier l'utilisation des ressources sur les nœuds :
     ```bash
     python3 resource_monitor.py
     ```

4. **Simuler les états du véhicule** :
   - Exécutez `vehicle_simulator.py` pour simuler les changements d'état du véhicule :
     ```bash
     python3 vehicle_simulator.py
     ```

5. **Vérifier les pods** :
   - Utilisez `kubectl get pods` pour voir les pods déployés sur le cluster.

## Notes importantes
- **Images Docker** : Les images `sdv-safety`, `sdv-comfort`, et `sdv-infotainment` doivent être construites et importées dans le cluster (via `run_baseline_local.sh`).
- **Nœuds** : Assurez-vous que les Raspberry Pi sont étiquetés avec les zones correspondantes (`zone=safety`, `zone=comfort`, `zone=infotainment`) pour que le `nodeSelector` fonctionne.
- **Dépendances** : Installez les dépendances listées dans `requirements.txt` avant d'exécuter les scripts Python.