#!/bin/bash

# === CONFIGURATION ===
CLUSTER_NAME="sdv-cluster"
KUBECONFIG_PATH="/etc/rancher/k3s/k3s.yaml"

echo "=== Déploiement SDV Baseline sur K3s ==="

echo "1. Vérification de l'installation K3s"
if ! command -v k3s &> /dev/null; then
    echo "Erreur: K3s n'est pas installé. Installation en cours..."
    curl -sfL https://get.k3s.io | sh -
    sudo systemctl enable k3s
    sudo systemctl start k3s
else
    echo "K3s détecté, redémarrage du service..."
    sudo systemctl restart k3s
fi

echo "2. Configuration de kubectl pour K3s"
export KUBECONFIG=$KUBECONFIG_PATH
sudo chmod 644 $KUBECONFIG_PATH

echo "3. Attente que K3s soit prêt"
kubectl wait --for=condition=Ready nodes --all --timeout=60s

echo "4. Build des images Docker locales"
if [ -d "docker/" ]; then
    cd docker/
    ./build_images.sh
    cd ..
else
    echo "Attention: Dossier docker/ introuvable, passage à l'étape suivante..."
fi

echo "5. Import des images dans le registry local K3s"
# K3s utilise containerd, donc on importe directement
sudo k3s ctr images import docker/sdv-safety.tar 2>/dev/null || echo "Image safety non trouvée"
sudo k3s ctr images import docker/sdv-comfort.tar 2>/dev/null || echo "Image comfort non trouvée" 
sudo k3s ctr images import docker/sdv-infotainment.tar 2>/dev/null || echo "Image infotainment non trouvée"

# Alternative si les images sont déjà dans Docker
sudo docker save sdv-safety | sudo k3s ctr images import - 2>/dev/null || echo "Import safety depuis Docker échoué"
sudo docker save sdv-comfort | sudo k3s ctr images import - 2>/dev/null || echo "Import comfort depuis Docker échoué"
sudo docker save sdv-infotainment | sudo k3s ctr images import - 2>/dev/null || echo "Import infotainment depuis Docker échoué"

echo "6. Déploiement des applications baseline"
if [ -d "k8s-manifests/" ]; then
    kubectl apply -f k8s-manifests/safety-apps/ 2>/dev/null || echo "Pas d'apps safety à déployer"
    kubectl apply -f k8s-manifests/comfort-apps/ 2>/dev/null || echo "Pas d'apps comfort à déployer"
    kubectl apply -f k8s-manifests/infotainment-apps/ 2>/dev/null || echo "Pas d'apps infotainment à déployer"
else
    echo "Attention: Dossier k8s-manifests/ introuvable"
fi

echo "7. Attente du déploiement des pods"
sleep 10

echo "8. État du cluster :"
echo "--- Nœuds ---"
kubectl get nodes
echo "--- Pods ---"
kubectl get pods --all-namespaces
echo "--- Services ---"
kubectl get services --all-namespaces

echo ""
echo "=== Déploiement terminé ! ==="
echo "• Pour suivre les logs : kubectl logs -f <nom-du-pod>"
echo "• Pour voir tous les pods : kubectl get pods -A"
echo "• Pour supprimer le déploiement : kubectl delete -f k8s-manifests/"
echo "• Pour arrêter K3s : sudo systemctl stop k3s"