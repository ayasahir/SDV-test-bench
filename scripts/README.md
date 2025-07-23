### 1. `setup_rpi_rt`
- **Rôle** : Configure les paramètres de base du système d'exploitation pour activer les fonctionnalités nécessaires à K3s sur chaque Raspberry Pi (maître et travailleurs).
- **Fonctions** :
  - Active les cgroups (control groups) pour la gestion des ressources (CPU, mémoire).
  - Configure les paramètres réseau pour Kubernetes (par exemple, `br_netfilter`).
  - Désactive le swap pour optimiser les performances du cluster.
- **Exécution** : Doit être exécuté sur chaque Raspberry Pi avant l'installation de K3s.
- **Interaction** : Prépare l'environnement système requis par `setup_k3s_master` et `setup_k3s_worker`.

### 2. `setup_rpi_rt_complete`
- **Rôle** : Complète la configuration initiale en installant des outils supplémentaires et en vérifiant la configuration système.
- **Fonctions** :
  - Installe des utilitaires comme `curl`, `iptables`, et autres dépendances nécessaires.
  - Vérifie que les paramètres réseau et cgroups sont correctement appliqués.
  - Configure les paramètres de performance pour éviter les erreurs liées aux ressources limitées des Raspberry Pi.
- **Exécution** : Exécuté après `setup_rpi_rt` sur chaque Raspberry Pi.
- **Interaction** : Complète la préparation amorcée par `setup_rpi_rt` et garantit que les nœuds sont prêts pour les scripts K3s.

### 3. `setup_k3s_master`
- **Rôle** : Installe et configure K3s sur le nœud maître du cluster Kubernetes.
- **Fonctions** :
  - Télécharge et installe K3s en mode serveur avec des paramètres spécifiques (par exemple, désactivation de Traefik, configuration d'une IP statique).
  - Génère un jeton (token) pour permettre aux nœuds travailleurs de rejoindre le cluster.
  - Configure les composants du plan de contrôle Kubernetes (API, Scheduler, Controller).
- **Exécution** : Exécuté uniquement sur le Raspberry Pi désigné comme nœud maître.
- **Interaction** : Produit un jeton utilisé par `setup_k3s_worker` pour connecter les nœuds travailleurs au maître.

### 4. `setup_k3s_worker`
- **Rôle** : Installe et configure K3s sur les nœuds travailleurs pour qu'ils rejoignent le cluster Kubernetes.
- **Fonctions** :
  - Installe K3s en mode agent.
  - Utilise l'URL du nœud maître et le jeton généré par `setup_k3s_master` pour rejoindre le cluster.
  - Configure les processus Kubernetes des travailleurs (Kubelet, kube-proxy).
- **Exécution** : Exécuté sur chaque Raspberry Pi désigné comme nœud travailleur.
- **Interaction** : Dépend du jeton et de l'URL fournis par `setup_k3s_master` pour établir la connexion avec le nœud maître.


1. **Préparation** : `setup_rpi_rt` et `setup_rpi_rt_complete` sont exécutés séquentiellement sur chaque Raspberry Pi pour préparer l'environnement système.
2. **Installation du maître** : `setup_k3s_master` est exécuté sur le nœud maître pour initialiser le cluster et générer le jeton.
3. **Connexion des travailleurs** : `setup_k3s_worker` utilise le jeton et l'URL du maître pour connecter les nœuds travailleurs au cluster.
4. **Ordre d'exécution** :
   - Sur chaque Raspberry Pi : `setup_rpi_rt` → `setup_rpi_rt_complete`.
   - Sur le nœud maître : `setup_k3s_master`.
   - Sur les nœuds travailleurs : `setup_k3s_worker`.

## Étapes pour utiliser les fichiers
1. **Configurer les Raspberry Pi** :
   - Flashez Raspberry Pi OS Lite (64 bits) sur chaque Raspberry Pi.
   - Configurez des adresses IP statiques et activez SSH.
2. **Exécuter les scripts de préparation** :
   - Sur chaque Raspberry Pi, exécutez `sudo bash setup_rpi_rt`.
   - Ensuite, exécutez `sudo bash setup_rpi_rt_complete`.
3. **Configurer le nœud maître** :
   - Sur le Raspberry Pi maître, exécutez `sudo bash setup_k3s_master`.
   - Notez le jeton généré (situé dans `/var/lib/rancher/k3s/server/node-token`).
4. **Configurer les nœuds travailleurs** :
   - Sur chaque Raspberry Pi travailleur, modifiez `setup_k3s_worker` pour inclure l'IP du maître et le jeton.
   - Exécutez `sudo bash setup_k3s_worker`.
5. **Vérifier le cluster** :
   - Sur le nœud maître, exécutez `sudo k3s kubectl get nodes` pour vérifier que tous les nœuds sont connectés et prêts.