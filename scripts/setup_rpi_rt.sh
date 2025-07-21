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
sudo apt update 

# Étape 3 - Installation des outils essentiels
echo -e "${GREEN}=== [3/8] Installation des outils essentiels ===${NC}"
sudo apt install -y curl wget git vim htop iotop nethogs iproute2 ethtool

# Étape 4 - Installation de Docker
echo -e "${GREEN}=== [4/8] Installation de Docker ===${NC}"
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Étape 5 - Installation du noyau temps réel PREEMPT-RT
#echo -e "${GREEN}=== [5/8] Installation du noyau PREEMPT-RT ===${NC}"
#echo "Installation du kernel temps réel pour support TSN..."
#sudo apt install -y raspberrypi-kernel-rt

# Étape 6 - Configuration réseau pour TSN/TAS
echo -e "${GREEN}=== [6/8] Configuration réseau TSN/TAS ===${NC}"
# Configuration pour simuler limitation de bande passante à 10Mbps
sudo apt install -y wondershaper

# Création du script de limitation réseau
cat << 'EOF' | sudo tee /usr/local/bin/setup_network_limit.sh > /dev/null
#!/bin/bash
# Script to limit network to 10Mbps for SDV test
# Run after boot when network is ready
LOG_FILE="/tmp/network_limit.log"
echo "[$(date)] Starting network limit" >> $LOG_FILE
# Check if tc is installed
if ! tc -V &> /dev/null; then
    echo "[ERROR] tc not found. Install it: sudo apt-get install iproute2" >> $LOG_FILE
    exit 1
fi
# Get network interface
INTERFACE=$(ip route get 8.8.8.8 | awk '{print $5; exit}')
if [ -z "$INTERFACE" ]; then
    echo "[ERROR] No network interface found. Check with: ip link" >> $LOG_FILE
    exit 1
fi
echo "[INFO] Using interface: $INTERFACE" >> $LOG_FILE
# Check if interface is up
if ! ip link show $INTERFACE | grep -q "state UP"; then
    echo "[ERROR] Interface $INTERFACE not up" >> $LOG_FILE
    exit 1
fi
# Clear old tc rules
tc qdisc del dev $INTERFACE root 2>/dev/null
echo "[INFO] Cleared old rules" >> $LOG_FILE
# Set 10Mbps limit
if tc qdisc add dev $INTERFACE root tbf rate 10mbit burst 32kbit latency 400ms; then
    echo "[SUCCESS] 10Mbps limit set" >> $LOG_FILE
else
    echo "[ERROR] Failed to set limit" >> $LOG_FILE
    exit 1
fi
# Show result
tc qdisc show dev $INTERFACE >> $LOG_FILE
echo "[$(date)] Done" >> $LOG_FILE
EOF

sudo chmod +x /usr/local/bin/setup_network_limit.sh

# Étape 7 - Configuration pour démarrage automatique
echo -e "${GREEN}=== [7/8] Configuration du démarrage automatique ===${NC}"


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
tc qdisc show dev $INTERFACE 2>/dev/null | grep -q tbf && echo "✓ Limitation réseau active" || echo "! Limitation réseau non active"

echo "=== Configuration terminée ==="
EOF

sudo chmod +x /usr/local/bin/verify_setup.sh

# Étape 8 - Instructions de redémarrage
echo -e "${GREEN}=== [8/8] Configuration terminée ===${NC}"
echo ""
echo -e "${YELLOW}  IMPORTANT ${NC}"
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
    echo "Run this after boot to limit network to 10Mbps:"
    echo "sudo /usr/local/bin/setup_network_limit.sh"
    sleep 1
done


echo "Redémarrage maintenant..."
sudo reboot
