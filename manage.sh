#!/bin/bash

# Script de gestion pour MonCampus ECAL Docker
# Système unifié multi-configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/configs"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function show_help() {
    echo -e "${BLUE}MonCampus ECAL Docker Manager${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build                 Construire les images Docker"
    echo "  start [config]        Démarrer les services (optionnel: config spécifique)"
    echo "  stop [config]         Arrêter les services (optionnel: config spécifique)"
    echo "  restart [config]      Redémarrer les services (optionnel: config spécifique)"
    echo "  logs [config]         Voir les logs (optionnel: config spécifique)"
    echo "  status               Voir le statut des services"
    echo "  clean                Nettoyer les containers et images"
    echo "  config               Lister les configurations disponibles"
    echo "  add-config           Ajouter une nouvelle configuration"
    echo "  generate-compose     Régénérer le docker-compose.yml"
    echo "  help                 Afficher cette aide"
    echo ""
    echo "Configurations:"
    echo "  default              Configuration par défaut (config.yml à la racine)"
    echo "  <nom>                Configuration spécifique (configs/<nom>.yml)"
    echo ""
    echo "Examples:"
    echo "  $0 build                    # Construire les images"
    echo "  $0 start                    # Démarrer toutes les instances"
    echo "  $0 start default            # Démarrer l'instance par défaut"
    echo "  $0 start config1            # Démarrer seulement l'instance config1"
    echo "  $0 logs config2             # Voir les logs de config2"
    echo "  $0 config                   # Lister les configurations"
    echo "  $0 generate-compose         # Régénérer docker-compose.yml"
}

function build_images() {
    echo -e "${YELLOW}Construction des images Docker...${NC}"
    ensure_compose_updated
    docker-compose build
}

function start_services() {
    local config_name=$1
    
    # S'assurer que le docker-compose.yml est à jour
    ensure_compose_updated
    
    if [ -z "$config_name" ]; then
        echo -e "${GREEN}Démarrage de toutes les instances...${NC}"
        docker-compose up -d
    elif [ "$config_name" = "default" ]; then
        echo -e "${GREEN}Démarrage de l'instance par défaut...${NC}"
        if [ ! -f "$SCRIPT_DIR/config.yml" ]; then
            echo -e "${RED}Erreur: Configuration par défaut non trouvée${NC}"
            exit 1
        fi
        docker-compose --profile default up -d app-default selenium
    else
        echo -e "${GREEN}Démarrage de l'instance $config_name...${NC}"
        if [ ! -f "$CONFIGS_DIR/${config_name}.yml" ]; then
            echo -e "${RED}Erreur: Configuration $config_name non trouvée${NC}"
            echo -e "${YELLOW}Configurations disponibles:${NC}"
            list_configs
            exit 1
        fi
        docker-compose up -d app-$config_name selenium
    fi
}

function stop_services() {
    local config_name=$1
    
    if [ -z "$config_name" ]; then
        echo -e "${YELLOW}Arrêt de tous les services...${NC}"
        docker-compose down
        docker-compose --profile default down
    elif [ "$config_name" = "default" ]; then
        echo -e "${YELLOW}Arrêt de l'instance par défaut...${NC}"
        docker-compose --profile default stop app-default
    else
        echo -e "${YELLOW}Arrêt de l'instance $config_name...${NC}"
        docker-compose stop app-$config_name
    fi
}

function restart_services() {
    local config_name=$1
    stop_services "$config_name"
    sleep 2
    start_services "$config_name"
}

function show_logs() {
    local config_name=$1
    
    if [ -z "$config_name" ]; then
        echo -e "${BLUE}Logs de tous les services:${NC}"
        docker-compose logs -f
        docker-compose --profile default logs -f
    elif [ "$config_name" = "default" ]; then
        echo -e "${BLUE}Logs de l'instance par défaut:${NC}"
        docker-compose --profile default logs -f app-default
    else
        echo -e "${BLUE}Logs de l'instance $config_name:${NC}"
        docker-compose logs -f app-$config_name
    fi
}

function show_status() {
    echo -e "${BLUE}Status des services:${NC}"
    docker-compose ps
    echo -e "${BLUE}Status du service par défaut:${NC}"
    docker-compose --profile default ps
}

function clean_all() {
    echo -e "${YELLOW}Nettoyage des containers et images...${NC}"
    docker-compose down --rmi all --volumes --remove-orphans
    docker-compose --profile default down --rmi all --volumes --remove-orphans
}

function list_configs() {
    echo -e "${BLUE}Configurations disponibles:${NC}"
    
    # Configuration par défaut
    if [ -f "$SCRIPT_DIR/config.yml" ]; then
        echo -e "  ${YELLOW}default${NC} (configuration par défaut)"
    fi
    
    # Configurations personnalisées
    if [ -d "$CONFIGS_DIR" ]; then
        for config_file in "$CONFIGS_DIR"/*.yml; do
            if [ -f "$config_file" ]; then
                config_name=$(basename "$config_file" .yml)
                echo -e "  ${GREEN}$config_name${NC}"
            fi
        done
    fi
    
    if [ ! -f "$SCRIPT_DIR/config.yml" ] && [ ! -d "$CONFIGS_DIR" ]; then
        echo -e "${RED}Aucune configuration trouvée${NC}"
    fi
}

function add_config() {
    echo -e "${BLUE}Ajout d'une nouvelle configuration...${NC}"
    read -p "Nom de la configuration (ex: config3): " config_name
    
    if [ -z "$config_name" ]; then
        echo -e "${RED}Nom de configuration requis${NC}"
        exit 1
    fi
    
    # Créer le dossier configs s'il n'existe pas
    mkdir -p "$CONFIGS_DIR"
    
    config_file="$CONFIGS_DIR/${config_name}.yml"
    
    if [ -f "$config_file" ]; then
        echo -e "${RED}La configuration $config_name existe déjà${NC}"
        exit 1
    fi
    
    cat > "$config_file" << EOF
# Configuration pour $config_name
moncampus_username: "votre_username_moncampus"
moncampus_password: "votre_password_moncampus"
moncampus_start_date: "2025-01-01"
moncampus_end_date: "2025-12-31"
ecal_api_key: "votre_api_key_ecal"
ecal_api_secret: "votre_api_secret_ecal"
ecal_calendar_id: "votre_calendar_id"
error_file_path: "/app/errors_${config_name}.txt"
instance_name: "$config_name"
EOF
    
    echo -e "${GREEN}Configuration $config_name créée dans $config_file${NC}"
    echo -e "${YELLOW}N'oubliez pas de modifier les valeurs avec vos vraies données !${NC}"
}

function regenerate_compose() {
    echo -e "${BLUE}Régénération du docker-compose.yml...${NC}"
    "$SCRIPT_DIR/generate-compose.sh"
}

function ensure_compose_updated() {
    # Vérifier si le docker-compose.yml est à jour avec les configurations
    local needs_update=false
    
    if [ -d "$CONFIGS_DIR" ]; then
        for config_file in "$CONFIGS_DIR"/*.yml; do
            if [ -f "$config_file" ]; then
                config_name=$(basename "$config_file" .yml)
                if ! grep -q "app-$config_name:" docker-compose.yml 2>/dev/null; then
                    needs_update=true
                    break
                fi
            fi
        done
    fi
    
    if [ "$needs_update" = true ]; then
        echo -e "${YELLOW}Nouvelles configurations détectées, régénération du docker-compose.yml...${NC}"
        regenerate_compose
    fi
}

# Vérifier que Docker et docker-compose sont installés
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker n'est pas installé${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}docker-compose n'est pas installé${NC}"
        exit 1
    fi
}

# Main script logic
case "$1" in
    build)
        check_dependencies
        build_images
        ;;
    start)
        check_dependencies
        start_services "$2"
        ;;
    stop)
        check_dependencies
        stop_services "$2"
        ;;
    restart)
        check_dependencies
        restart_services "$2"
        ;;
    logs)
        check_dependencies
        show_logs "$2"
        ;;
    status)
        check_dependencies
        show_status
        ;;
    clean)
        check_dependencies
        clean_all
        ;;
    config)
        list_configs
        ;;
    add-config)
        add_config
        ;;
    generate-compose)
        regenerate_compose
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Commande inconnue: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
