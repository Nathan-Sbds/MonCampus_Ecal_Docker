#!/bin/bash

# Script pour configurer et démarrer les cronjobs
CONFIG_FILE=${CONFIG_FILE:-"/app/config.yml"}
INSTANCE_NAME=${INSTANCE_NAME:-"default"}

echo "Configuration des cronjobs pour l'instance: $INSTANCE_NAME"
echo "Fichier de configuration: $CONFIG_FILE"

# Vérifier que le fichier de configuration existe
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERREUR: Fichier de configuration $CONFIG_FILE non trouvé"
    exit 1
fi

# Créer le cronjob pour cette instance spécifique
CRONJOB_FILE="/tmp/cronjob_$INSTANCE_NAME"
echo "46 6-18 * * * /bin/bash -c \"/app/venv/bin/python3 /app/agenda.py $CONFIG_FILE >> /var/log/cron_$INSTANCE_NAME.log 2>&1\"" > $CRONJOB_FILE

# Installer le cronjob
crontab $CRONJOB_FILE

echo "Cronjob configuré pour l'instance $INSTANCE_NAME :"
crontab -l

# Démarrer cron en mode daemon
echo "Démarrage du service cron..."
exec cron -f
