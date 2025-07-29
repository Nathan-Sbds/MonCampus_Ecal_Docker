#!/bin/bash

# Script pour générer automatiquement docker-compose.yml basé sur les configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/configs"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Couleurs pour l'affichage
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Génération automatique du docker-compose.yml...${NC}"

# Début du fichier docker-compose.yml
cat > "$COMPOSE_FILE" << 'EOF'
services:
EOF

# Ajouter les services pour chaque configuration
if [ -d "$CONFIGS_DIR" ]; then
    for config_file in "$CONFIGS_DIR"/*.yml; do
        if [ -f "$config_file" ]; then
            config_name=$(basename "$config_file" .yml)
            echo -e "${GREEN}Ajout du service pour la configuration: $config_name${NC}"
            
            cat >> "$COMPOSE_FILE" << EOF
  # Service pour la configuration $config_name
  app-$config_name:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: moncampusecal-$config_name
    depends_on:
      - selenium
    volumes:
      - ./configs/$config_name.yml:/app/config.yml:ro
    environment:
      - CONFIG_FILE=/app/config.yml
      - INSTANCE_NAME=$config_name
    networks:
      - selenium_network
    restart: always

EOF
        fi
    done
fi

# Ajouter le service par défaut
echo -e "${GREEN}Ajout du service par défaut${NC}"
cat >> "$COMPOSE_FILE" << 'EOF'
  # Service par défaut utilisant config.yml de base
  app-default:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: moncampusecal-default
    depends_on:
      - selenium
    volumes:
      - ./config.yml:/app/config.yml:ro
    environment:
      - CONFIG_FILE=/app/config.yml
      - INSTANCE_NAME=default
    networks:
      - selenium_network
    restart: always
    profiles: ["default"]

  # Service Selenium partagé
  selenium:
    image: selenium/standalone-firefox:4.27.0
    environment:
      - SE_NODE_HOST=localhost
      - SE_NODE_PORT=5555
      - SE_ENABLE_TRACING=false
    ports:
      - "4444:4444"
    networks:
      - selenium_network

networks:
  selenium_network:
    driver: bridge
EOF

echo -e "${YELLOW}docker-compose.yml généré avec succès !${NC}"
echo -e "${BLUE}Services générés pour les configurations:${NC}"

# Lister les configurations trouvées
if [ -d "$CONFIGS_DIR" ]; then
    for config_file in "$CONFIGS_DIR"/*.yml; do
        if [ -f "$config_file" ]; then
            config_name=$(basename "$config_file" .yml)
            echo -e "  - ${GREEN}$config_name${NC}"
        fi
    done
fi

echo -e "  - ${YELLOW}default${NC} (configuration par défaut)"
