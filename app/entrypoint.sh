#!/bin/sh

# Démarrer le service cron
service cron start

# Garder le conteneur en cours d'exécution
tail -f /dev/null