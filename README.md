# MonCampus_Ecal_Docker

Ce projet configure un conteneur Docker pour synchroniser les événements entre MonCampus et l'API ecal.com. Le conteneur utilise Python et plusieurs dépendances pour récupérer, formater et synchroniser les événements.

## Prérequis

- Docker installé sur votre machine

## Installation

1. Clonez ce dépôt sur votre machine locale.
2. Placez-vous dans le répertoire du projet.
3. Construisez l'image Docker.
```
docker build -t MonCampus_Ecal_Docker .
```
4. Créez et démarrez un conteneur à partir de l'image.
```
docker run -d --name MonCampus_Ecal_Docker_Container MonCampus_Ecal_Docker
```
## Configuration

Le fichier `config.json` doit être configuré avec vos informations personnelles et les clés API nécessaires.

```json
{
    "MONCAMPUS_USERNAME": "Username of MonCampus",
    "MONCAMPUS_PASSWORD": "Password of MonCampus", 
    "MONCAMPUS_START_DATE": "Start date of fetching events from MonCampus",
    "MONCAMPUS_END_DATE": "End date of fetching events from MonCampus",
    "CHROMIUM_EXECUTABLE_PATH": "/usr/bin/chromium-browser", 
    "ECAL_API_KEY": "Your API Key from ecal.com", 
    "ECAL_API_SECRET": "Your API Secret from ecal.com", 
    "ECAL_CALENDAR_ID": "Your Calendar ID from ecal.com",
    "ERROR_FILE_PATH": "/app/errors.txt"
}
```

## Utilisation

Le conteneur démarre un service cron qui exécute le script de synchronisation des événements à des intervalles réguliers définis dans le fichier `cronjob`.

## Fonctionnalités
 - Récupération des événements : Le script se connecte à MonCampus pour récupérer les événements dans la plage de dates spécifiée.
 - Formatage des événements : Les événements récupérés sont formatés pour être compatibles avec l'API ecal.com.
 - Synchronisation des événements : Les événements formatés sont envoyés à l'API ecal.com pour être ajoutés au calendrier spécifié.
 - Suppression des doublons : Le script vérifie et supprime les événements en double dans l'API ecal.com.
 - Vérification de la cohérence : Le script compare le nombre d'événements entre MonCampus et l'API ecal.com pour s'assurer qu'ils sont synchronisés.

## Dépendances
Les dépendances Python nécessaires sont listées dans le fichier `requirements.txt` et sont installées lors de la construction de l'image Docker.

## Structure du projet
 - `Dockerfile`: Définit l'image Docker.
 - `config.json`: Contient les configurations nécessaires.
 - `app/requirements.txt`: Liste des dépendances Python.
 - `app/entrypoint.sh`: Script d'entrée pour démarrer le service cron.
 - `app/cronjob`: Définit les tâches cron.
 - `app/agenda.py`: Script principal pour la synchronisation des événements.

## Auteurs
Ce projet a été réalisé par **SABOT DRESSY Nathan**.
