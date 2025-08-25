#!/bin/bash

# === CONFIGURATION ===
CLUSTER_NAME="sdv-cluster"

echo "1. (Re)Créer le cluster K3d local"
k3d cluster delete $CLUSTER_NAME 2>/dev/null
k3d cluster create $CLUSTER_NAME --agents 1 --servers 1

echo "2. Build des images Docker locales"
cd docker/
./build_images.sh
cd ..

echo "3. Import des images dans K3d"
k3d image import sdv-safety sdv-comfort sdv-infotainment -c $CLUSTER_NAME

echo "4. Déploiement des applications baseline"
kubectl apply -f k8s-manifests/safety-apps/
kubectl apply -f k8s-manifests/comfort-apps/
kubectl apply -f k8s-manifests/infotainment-apps/

echo "5. Liste des pods :"
kubectl get pods

echo "Test baseline déployé ! Tu peux suivre avec : kubectl logs -f <pod>"
