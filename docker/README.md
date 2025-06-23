# Docker Images - SDV Testbench

🐳 **Images Docker personnalisées pour applications véhicule SDV**

Ce dossier contient les Dockerfiles et simulateurs pour créer des images d'applications véhicule réalistes, remplaçant les simples containers `busybox` par des simulateurs sophistiqués.

## 📦 Images disponibles

| Image | Catégorie | Priorité | Description |
|-------|-----------|----------|-------------|
| `sdv-safety` | Safety | Critique | Applications de sécurité temps réel |
| `sdv-comfort` | Comfort | Moyenne | Applications de confort et commodité |
| `sdv-infotainment` | Infotainment | Basse | Applications multimédia et divertissement |

## 🏗️ Structure

```
docker/
├── Dockerfile.base          # Image de base (non utilisée actuellement)
├── Dockerfile.safety        # Applications safety critiques
├── Dockerfile.comfort       # Applications comfort
├── Dockerfile.infotainment  # Applications infotainment
├── safety_simulator.py      # Simulateur applications safety
├── comfort_simulator.py     # Simulateur applications comfort
├── infotainment_simulator.py # Simulateur applications infotainment
├── docker-compose.yml       # Test local avec Docker Compose
├── build_images.sh          # Script de build automatisé
└── README.md                # Cette documentation
```

## 🚀 Utilisation rapide

### 1. Build des images

```bash
cd docker/
chmod +x build_images.sh
./build_images.sh
```

### 2. Test local avec Docker Compose

```bash
# Démarrer quelques applications
docker-compose up

# Démarrer en arrière-plan
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

### 3. Test d'une application spécifique

```bash
# Application safety
docker run -it --rm -e APP_NAME=emergency-brake sdv-safety:latest

# Application comfort  
docker run -it --rm -e APP_NAME=climate-control sdv-comfort:latest

# Application infotainment
docker run -it --rm -e APP_NAME=media-player sdv-infotainment:latest
```

## 🔧 Applications simulées

### Safety (Sécurité)
- **emergency-brake** : Freinage d'urgence (10ms response time)
- **collision-avoidance** : Évitement de collision (50ms)
- **lane-keeping** : Maintien de voie (100ms)
- **driver-monitoring** : Surveillance conducteur (200ms)

Simule : Capteurs radar/caméra, interventions automatiques, alertes critiques

### Comfort (Confort)
- **climate-control** : Contrôle climatique (2s update)
- **seat-adjustment** : Ajustement sièges (5s update)
- **lighting-control** : Contrôle éclairage (3s)
- **parking-assist** : Aide au stationnement (100ms)
- **navigation-basic** : Navigation de base (1s)

Simule : Capteurs environnement, ajustements automatiques, requêtes utilisateur

### Infotainment (Divertissement)
- **media-player** : Lecteur multimédia (2 Mbps, 1s update)
- **streaming-video** : Streaming vidéo (5 Mbps, 500ms)
- **games-engine** : Moteur de jeux (3 Mbps, 16ms/60fps)
- **social-media** : Réseaux sociaux (2.5 Mbps, 2s)
- **web-browser** : Navigateur web (3.5 Mbps, 1s)
- **music-streaming** : Streaming musical (1.5 Mbps, 1s)

Simule : Traitement multimédia, interactions utilisateur, utilisation bande passante

## 🎛️ Variables d'environnement

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `APP_NAME` | Nom de l'application à simuler | Selon l'image |
| `SDV_PRIORITY` | Priorité de l'application | critical/medium/low |
| `SDV_REAL_TIME` | Mode temps réel | true/false |
| `HOSTNAME` | Nom du pod/container | Automatique |

## 📊 Métriques simulées

### Safety Applications
- Cycles de traitement
- Alertes générées
- Interventions automatiques
- Temps de réponse

### Comfort Applications  
- Ajustements effectués
- Requêtes utilisateur
- État des actuateurs
- Cycles d'optimisation

### Infotainment Applications
- Contenu lu/streamé
- Interactions utilisateur
- Données traitées (MB)
- Utilisation bande passante

## 🔄 Intégration avec Kubernetes

Les images sont automatiquement utilisées par les manifestes K8s si vous les construisez localement :

```bash
# Build des images
./docker/build_images.sh

# Les manifestes K8s utiliseront automatiquement ces images
kubectl apply -f k8s-manifests/
```

## 🛠️ Développement

### Modifier un simulateur

1. Éditez le fichier Python correspondant (`*_simulator.py`)
2. Rebuild l'image : `docker build -f Dockerfile.safety -t sdv-safety:latest .`
3. Testez : `docker run -e APP_NAME=emergency-brake sdv-safety:latest`

### Ajouter une nouvelle application

1. Ajoutez la configuration dans le simulateur approprié
2. Mettez à jour le manifeste K8s correspondant
3. Rebuild l'image

### Personnaliser les Dockerfiles

Les Dockerfiles sont optimisés pour Raspberry Pi (architecture ARM). Pour d'autres architectures, vous pouvez :

- Changer l'image de base (`FROM alpine:3.18`)
- Ajuster les paquets installés
- Modifier les bibliothèques Python

## 🐛 Dépannage

### Images non trouvées
```bash
# Vérifier les images disponibles
docker images | grep sdv

# Rebuild si nécessaire
./build_images.sh
```

### Erreurs de permissions
```bash
# Rendre exécutable
chmod +x build_images.sh

# Vérifier Docker daemon
docker info
```

### Applications ne démarrent pas
```bash
# Vérifier les logs
docker logs <container_name>

# Tester manuellement
docker run -it --rm sdv-safety:latest bash
```

## 📈 Avantages vs. busybox

| Caractéristique | busybox | Images SDV |
|-----------------|---------|------------|
| **Réalisme** | Messages simples | Simulation complète |
| **Métriques** | Aucune | Détaillées |
| **Comportement** | Statique | Dynamique |
| **Débogage** | Limité | Logs détaillés |
| **Tests** | Basique | Scénarios réalistes |

Les nouvelles images permettent un testbench bien plus représentatif du comportement réel des applications véhicule SDV !

---

**🎯 Prêt pour simulation réaliste d'applications véhicule !** 