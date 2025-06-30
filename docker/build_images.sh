#!/bin/bash

# SDV Testbench - Script de build des images Docker
# Construit toutes les images personnalisées pour le testbench

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGISTRY_PREFIX=${REGISTRY_PREFIX:-"sdv-testbench"}
TAG=${TAG:-"latest"}

echo -e "${BLUE}=== SDV Testbench - Build Images Docker ===${NC}"
echo "Registry prefix: $REGISTRY_PREFIX"
echo "Tag: $TAG"
echo ""

# Fonction de build
build_image() {
    local dockerfile=$1
    local image_name=$2
    local category=$3
    
    echo -e "${GREEN}Building $image_name ($category)...${NC}"
    
    if docker build -f $dockerfile -t ${REGISTRY_PREFIX}/${image_name}:${TAG} .; then
        echo -e "${GREEN} $image_name built successfully${NC}"
        
        # Tagging pour usage local
        docker tag ${REGISTRY_PREFIX}/${image_name}:${TAG} ${image_name}:${TAG}
        
        return 0
    else
        echo -e "${RED} Failed to build $image_name${NC}"
        return 1
    fi
}

# Build des images spécialisées
echo -e "${YELLOW}Building specialized SDV images...${NC}"

# Image Safety
build_image "docker/Dockerfile.safety" "sdv-safety" "Safety Applications"

# Image Comfort  
build_image "docker/Dockerfile.comfort" "sdv-comfort" "Comfort Applications"

# Image Infotainment
build_image "docker/Dockerfile.infotainment" "sdv-infotainment" "Infotainment Applications"

echo ""
echo -e "${GREEN}=== Build Summary ===${NC}"
docker images | grep -E "(sdv-|REPOSITORY)" | head -10

echo ""
echo -e "${GREEN}=== Images built successfully! ===${NC}"
echo ""
echo "Available images:"
echo "  • ${REGISTRY_PREFIX}/sdv-safety:${TAG}"
echo "  • ${REGISTRY_PREFIX}/sdv-comfort:${TAG}"  
echo "  • ${REGISTRY_PREFIX}/sdv-infotainment:${TAG}"
echo ""
echo "Usage examples:"
echo "  # Test locally with docker-compose"
echo "  docker-compose up"
echo ""
echo "  # Run individual container"
echo "  docker run -e APP_NAME=emergency-brake sdv-safety:${TAG}"
echo ""
echo "  # Push to registry (if configured)"
echo "  docker push ${REGISTRY_PREFIX}/sdv-safety:${TAG}"

# Test rapide des images
echo ""
echo -e "${YELLOW}Quick test of built images...${NC}"

for image in "sdv-safety" "sdv-comfort" "sdv-infotainment"; do
    echo -n "Testing $image: "
    if docker run --rm -e APP_NAME=test ${image}:${TAG} python3 -c "print('OK')" &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
done

echo ""
echo -e "${GREEN}Docker images ready for SDV testbench!${NC}" 