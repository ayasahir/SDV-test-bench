#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Installation K3s Master pour SDV Testbench ===${NC}"
echo "Configuration de l'orchestrateur principal"
echo ""

# Vérification des prérequis
echo -e "${GREEN}=== [1/6] Vérification des prérequis ===${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker n'est pas installé${NC}"
    echo "Lancez d'abord: ./setup_rpi_rt.sh"
    exit 1
fi

if [ "$(hostname)" != "orchestrator-node" ]; then
    echo -e "${YELLOW}⚠️  Hostname actuel: $(hostname)${NC}"
    echo "Ce script doit être lancé sur le nœud orchestrateur"
    read -p "Continuer quand même? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✓ Prérequis validés"

# Installation K3s master
echo -e "${GREEN}=== [2/6] Installation K3s Master ===${NC}"
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=traefik --node-label role=orchestrator" sh -

# Attendre que K3s soit prêt
echo "Attente du démarrage de K3s..."
for i in {1..30}; do
    if sudo kubectl get nodes &>/dev/null; then
        break
    fi
    sleep 2
    echo -n "."
done
echo ""

# Vérification de l'installation
echo -e "${GREEN}=== [3/6] Vérification de l'installation ===${NC}"
sudo kubectl get nodes
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Erreur lors de l'installation K3s${NC}"
    exit 1
fi

# Configuration kubectl pour l'utilisateur
echo -e "${GREEN}=== [4/6] Configuration kubectl pour l'utilisateur ===${NC}"
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
export KUBECONFIG=~/.kube/config
echo 'export KUBECONFIG=~/.kube/config' >> ~/.bashrc

# Affichage des informations de connexion
echo -e "${GREEN}=== [5/6] Informations de connexion ===${NC}"
NODE_TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)
NODE_IP=$(hostname -I | awk '{print $1}')

echo "Informations pour connecter les workers:"
echo -e "${YELLOW}Token:${NC} $NODE_TOKEN"
echo -e "${YELLOW}IP Master:${NC} $NODE_IP"
echo -e "${YELLOW}URL:${NC} https://$NODE_IP:6443"

# Sauvegarde des informations
cat << EOF > ~/k3s-join-info.txt
# Informations pour joindre ce cluster K3s
# Utilisez ces informations sur les nœuds workers

export K3S_URL="https://$NODE_IP:6443"
export K3S_TOKEN="$NODE_TOKEN"

# Commande pour les workers:
# curl -sfL https://get.k3s.io | K3S_URL="https://$NODE_IP:6443" K3S_TOKEN="$NODE_TOKEN" sh -
EOF

echo "Informations sauvegardées dans: ~/k3s-join-info.txt"

# Installation des outils de monitoring
echo -e "${GREEN}=== [6/6] Installation des outils de monitoring ===${NC}"

# Création du namespace pour le testbench
kubectl create namespace sdv-testbench 2>/dev/null || true

# Déploiement de metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo ""
echo -e "${GREEN}✓ Installation K3s Master terminée${NC}"
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo "1. Connecter les workers avec le script setup_k3s_worker.sh"
echo "2. Vérifier: kubectl get nodes"
echo "3. Lancer AXIL: cd ~/axil && python3 axil_complete.py"
echo ""
echo -e "${YELLOW}Commandes utiles:${NC}"
echo "• kubectl get nodes -o wide"
echo "• kubectl get pods --all-namespaces"
echo "• sudo systemctl status k3s"
