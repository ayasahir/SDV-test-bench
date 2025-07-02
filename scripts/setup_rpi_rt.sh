#!/bin/bash

# Couleurs pour l'affichage
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Setup Raspberry Pi pour Testbench SDV ===${NC}"
echo "Configuration avec noyau temps réel pour TSN/TAS support"
echo ""

# Étape 0 - Sélection du rôle
echo "Sélectionnez le rôle de ce Raspberry Pi :"
select role in "orchestrator-node" "node-safety" "node-comfort" "node-infotainment" "exit"; do
    case $role in
        orchestrator-node|node-safety|node-comfort|node-infotainment)
            echo -e "${GREEN}→ Rôle sélectionné : $role${NC}"
            break
            ;;
        exit)
            echo "Installation annulée."
            exit 0
            ;;
        *)
            echo -e "${RED}Choix invalide. Veuillez réessayer.${NC}"
            ;;
    esac
done

# Étape 1 - Configuration du hostname
echo -e "${GREEN}=== [1/8] Configuration du hostname ===${NC}"
echo "Ancien hostname: $(hostname)"
sudo hostnamectl set-hostname $role
echo "Nouveau hostname: $role"

# Étape 2 - Mise à jour du système
echo -e "${GREEN}=== [2/8] Mise à jour du système ===${NC}"
sudo apt update && sudo apt upgrade -y

# Étape 3 - Installation des outils essentiels
echo -e "${GREEN}=== [3/8] Installation des outils essentiels ===${NC}"
sudo apt install -y curl wget git vim htop iotop nethogs tc iproute2 ethtool

# Étape 4 - Installation de Docker
echo -e "${GREEN}=== [4/8] Installation de Docker ===${NC}"
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Étape 5 - Installation du noyau temps réel PREEMPT-RT
echo -e "${GREEN}=== [5/8] Installation du noyau PREEMPT-RT ===${NC}"
echo "Installation du kernel temps réel pour support TSN..."
sudo apt install -y raspberrypi-kernel-rt

# Étape 6 - Configuration réseau pour TSN/TAS
echo -e "${GREEN}=== [6/8] Configuration réseau TSN/TAS ===${NC}"
# Configuration pour simuler limitation de bande passante à 10Mbps
sudo apt install -y wondershaper

# Création du script de limitation réseau
cat << 'EOF' | sudo tee /usr/local/bin/setup_network_limit.sh > /dev/null
#!/bin/bash
# Script pour limiter la bande passante à 10Mbps (simulation TAS)
INTERFACE=$(ip route get 8.8.8.8 | awk '{print $5; exit}')
echo "Configuration TSN/TAS sur interface: $INTERFACE"
# Limitation à 10Mbps down/up
sudo wondershaper $INTERFACE 10000 10000
echo "Limite réseau appliquée: 10Mbps"
EOF

sudo chmod +x /usr/local/bin/setup_network_limit.sh

# Étape 7 - Configuration pour démarrage automatique
echo -e "${GREEN}=== [7/8] Configuration du démarrage automatique ===${NC}"

# Service pour limitation réseau au boot
cat << EOF | sudo tee /etc/systemd/system/sdv-network-limit.service > /dev/null
[Unit]
Description=SDV Network Bandwidth Limitation (TSN/TAS Simulation)
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/setup_network_limit.sh
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable sdv-network-limit.service

# Script de vérification post-reboot
cat << 'EOF' | sudo tee /usr/local/bin/verify_setup.sh > /dev/null
#!/bin/bash
echo "=== Vérification de la configuration SDV ==="
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "Docker: $(docker --version 2>/dev/null || echo 'Non installé')"
echo "Noyau RT: $(zcat /proc/config.gz 2>/dev/null | grep PREEMPT_RT || echo 'CONFIG non accessible')"

# Test Docker
echo "Test Docker..."
docker run --rm hello-world >/dev/null 2>&1 && echo "✓ Docker fonctionne" || echo "✗ Docker KO"

# Test limitation réseau
INTERFACE=$(ip route get 8.8.8.8 | awk '{print $5; exit}')
echo "Interface réseau: $INTERFACE"
tc qdisc show dev $INTERFACE 2>/dev/null | grep -q wondershaper && echo "✓ Limitation réseau active" || echo "! Limitation réseau non active"

echo "=== Configuration terminée ==="
EOF

sudo chmod +x /usr/local/bin/verify_setup.sh

# Étape 8 - Instructions de redémarrage
echo -e "${GREEN}=== [8/8] Configuration terminée ===${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT ⚠️${NC}"
echo "Le système va redémarrer dans 10 secondes pour activer:"
echo "  → Noyau temps réel (PREEMPT-RT)"
echo "  → Configuration Docker"
echo "  → Limitation réseau TSN/TAS (10Mbps)"
echo ""
echo "Après redémarrage, reconnectez-vous et tapez:"
echo -e "${GREEN}sudo /usr/local/bin/verify_setup.sh${NC}"
echo ""

for i in {10..1}; do
    echo -ne "Redémarrage dans $i secondes...\r"
    sleep 1
done

echo "Redémarrage maintenant..."
sudo reboot
