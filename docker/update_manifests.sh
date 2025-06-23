#!/bin/bash

# SDV Testbench - Mise à jour des manifestes K8s
# Met à jour tous les manifestes pour utiliser les images Docker personnalisées

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Mise à jour des manifestes K8s pour images SDV ===${NC}"
echo ""

# Fonction de mise à jour des images
update_manifests() {
    local category=$1
    local image_name=$2
    local manifest_dir=$3
    
    echo -e "${YELLOW}Mise à jour $category applications...${NC}"
    
    if [ ! -d "$manifest_dir" ]; then
        echo -e "${RED}✗ Dossier $manifest_dir non trouvé${NC}"
        return 1
    fi
    
    # Mise à jour des images busybox vers images SDV
    find "$manifest_dir" -name "*.yaml" -exec sed -i "s|image: busybox:latest|image: $image_name:latest|g" {} \;
    find "$manifest_dir" -name "*.yaml" -exec sed -i "/image: $image_name:latest/a\\        imagePullPolicy: IfNotPresent" {} \;
    
    # Suppression des anciennes commandes busybox
    find "$manifest_dir" -name "*.yaml" -exec sed -i '/command: \["sh", "-c"\]/d' {} \;
    find "$manifest_dir" -name "*.yaml" -exec sed -i '/args: \[.*echo.*\]/d' {} \;
    
    echo -e "${GREEN}✓ $category manifestes mis à jour${NC}"
}

# Sauvegarde des manifestes originaux
echo "Création de sauvegarde des manifestes..."
if [ ! -d "../k8s-manifests-backup" ]; then
    cp -r ../k8s-manifests ../k8s-manifests-backup
    echo -e "${GREEN}✓ Sauvegarde créée dans k8s-manifests-backup/${NC}"
fi

# Mise à jour par catégorie
update_manifests "Safety" "sdv-safety" "../k8s-manifests/safety-apps"
update_manifests "Comfort" "sdv-comfort" "../k8s-manifests/comfort-apps"  
update_manifests "Infotainment" "sdv-infotainment" "../k8s-manifests/infotainment-apps"

echo ""
echo -e "${GREEN}=== Mise à jour terminée ===${NC}"
echo ""
echo "Modifications effectuées:"
echo "  • Images busybox remplacées par images SDV personnalisées"
echo "  • Politique imagePullPolicy ajoutée"
echo "  • Anciennes commandes busybox supprimées"
echo ""
echo "Images utilisées:"
echo "  • Safety: sdv-safety:latest"
echo "  • Comfort: sdv-comfort:latest"
echo "  • Infotainment: sdv-infotainment:latest"
echo ""
echo "Pour appliquer les changements:"
echo "  kubectl apply -f ../k8s-manifests/"
echo ""
echo "Pour revenir aux manifestes originaux:"
echo "  cp -r ../k8s-manifests-backup/* ../k8s-manifests/"

# Vérification des changements
echo ""
echo -e "${YELLOW}Vérification des images dans les manifestes:${NC}"
grep -r "image: sdv-" ../k8s-manifests/ | wc -l | xargs echo "Images SDV trouvées:"
grep -r "image: busybox" ../k8s-manifests/ | wc -l | xargs echo "Images busybox restantes:"

echo ""
echo -e "${GREEN}Manifestes prêts pour le testbench SDV réaliste !${NC}" 