#!/bin/bash

# SDV Testbench - Script de setup complet pour Raspberry Pi
# Version finale avec toutes les optimisations

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== SDV Testbench - Setup Raspberry Pi Complet ===${NC}"
echo "Ceci est la version alternative du script de setup"
echo "Pour le script principal, utilisez: ./setup_rpi_rt.sh"
echo ""

# Rendre tous les scripts exécutables
echo -e "${GREEN}Mise à jour des permissions des scripts...${NC}"
chmod +x *.sh
chmod +x ../tests/*.sh

echo -e "${GREEN}Tous les scripts sont maintenant exécutables${NC}"
echo ""
echo "Scripts disponibles:"
echo "  • setup_rpi_rt.sh        - Setup principal Raspberry Pi"
echo "  • setup_k3s_master.sh    - Setup K3s master"
echo "  • setup_k3s_worker.sh    - Setup K3s workers"
echo "  • ../tests/test_full_deployment.sh - Test complet"
echo ""
echo "Prochaine étape: Lancez ./setup_rpi_rt.sh"
