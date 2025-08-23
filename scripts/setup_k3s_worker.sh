#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Installation K3s Worker pour SDV Testbench ===${NC}"
echo "Configuration d'un nœud worker"
echo ""

# Détection automatique du rôle basé sur le hostname
HOSTNAME=$(hostname)
echo "Hostname détecté: $HOSTNAME"

case $HOSTNAME in
    node-safety)
        ZONE="safety"
        ;;
    node-comfort)
        ZONE="comfort"
        ;;
    node-infotainment)
        ZONE="infotainment"
        ;;
    *)
        echo -e "${RED}✗ Hostname non reconnu: $HOSTNAME${NC}"
        echo "Hostnames acceptés: node-safety, node-comfort, node-infotainment"
        echo "Configurez le hostname avec: sudo hostnamectl set-hostname node-XXX"
        exit 1
        ;;
esac

echo -e "${GREEN}→ Zone assignée: $ZONE${NC}"

# Demande des informations de connexion
echo -e "${GREEN}=== [1/5] Configuration de la connexion au master ===${NC}"

# Tentative de lecture automatique si le fichier existe
if [ -f ~/k3s-join-info.txt ]; then
    echo "Fichier de configuration trouvé, lecture automatique..."
    source ~/k3s-join-info.txt
    echo "URL: $K3S_URL"
    echo "Token: ${K3S_TOKEN:0:10}..."
else
    echo "Entrez les informations du master K3s:"
    read -p "IP du master: " MASTER_IP
    read -p "Token du master: " K3S_TOKEN
    K3S_URL="https://$MASTER_IP:6443"
fi

# Validation des paramètres
if [ -z "$K3S_URL" ] || [ -z "$K3S_TOKEN" ]; then
    echo -e "${RED}✗ URL ou Token manquant${NC}"
    exit 1
fi

# Vérification des prérequis
echo -e "${GREEN}=== [2/5] Vérification des prérequis ===${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker n'est pas installé${NC}"
    echo "Lancez d'abord: ./setup_rpi_rt.sh"
    exit 1
fi

echo "✓ Prérequis validés"

# Test de connectivité au master
echo -e "${GREEN}=== [3/5] Test de connectivité au master ===${NC}"
MASTER_IP=$(echo $K3S_URL | sed 's|https://||' | sed 's|:6443||')
ping -c 1 $MASTER_IP &>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Impossible de ping le master $MASTER_IP${NC}"
    echo "Vérifiez la connectivité réseau"
    read -p "Continuer quand même? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Installation K3s worker
echo -e "${GREEN}=== [4/5] Installation K3s Worker ===${NC}"
echo "Connexion au cluster: $K3S_URL"

if ! curl -sfL https://get.k3s.io | K3S_URL="$K3S_URL" K3S_TOKEN="$K3S_TOKEN" INSTALL_K3S_EXEC="..." sh -; then
    echo -e "${RED}✗ Échec installation K3s worker${NC}"
    cleanup_k3s_worker
    exit 1
fi

# Attente avec vérification d'échec
for i in {1..30}; do
    sudo systemctl is-active --quiet k3s-agent && break
    sleep 2
done

if [ $i -eq 30 ]; then
    echo -e "${RED}✗ Service k3s-agent non démarré${NC}"
    cleanup_k3s_worker  # ← Rollback après échec
    exit 1
fi

cleanup_k3s_worker() {
    sudo systemctl stop k3s-agent 2>/dev/null || true
    sudo /usr/local/bin/k3s-agent-uninstall.sh 2>/dev/null || true
}

# Vérification de l'installation
echo -e "${GREEN}=== [5/5] Vérification de l'installation ===${NC}"

# Attendre que le service soit prêt
echo "Attente du démarrage de K3s..."
for i in {1..30}; do
    if sudo systemctl is-active --quiet k3s-agent; then
        echo "✓ Service K3s actif"
        break
    fi
    sleep 2
    echo -n "."
done
echo ""

# Vérifier la connexion au cluster (depuis le master)
echo ""
echo -e "${GREEN}✓ Installation K3s Worker terminée${NC}"
echo ""
echo -e "${YELLOW}Configuration appliquée:${NC}"
echo "• Zone: $ZONE"
echo "• Rôle: worker"
echo "• Master: $MASTER_IP"
echo ""
echo -e "${YELLOW}Vérifications à faire depuis le master:${NC}"
echo "• kubectl get nodes -o wide"
echo "• kubectl get nodes --show-labels"
echo "• kubectl describe node $HOSTNAME"
echo ""
echo -e "${YELLOW}Commandes utiles sur ce nœud:${NC}"
echo "• sudo systemctl status k3s-agent"
echo "• sudo journalctl -u k3s-agent -f"
echo "• docker ps"
