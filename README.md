# MonCampus_Ecal_Docker

Ce projet configure un conteneur Docker pour synchroniser les événements entre MonCampus et l'API ecal.com. Le conteneur utilise Python et plusieurs dépendances pour récupérer, formater et synchroniser les événements.

## Prérequis

- Docker installé sur votre machine

## Configuration

Le fichier `config.yml` doit être configuré avec vos informations personnelles et les clés API nécessaires. Veuillez ne pas modifier la valeur de `error_file_path` si vous ne savez pas ce que vous faites.

```yaml
[CONFIG]
moncampus_username: Username of MonCampus
moncampus_password: Password of MonCampus
moncampus_start_date: Start date of fetching events from MonCampus
moncampus_end_date: End date of fetching events from MonCampus
ecal_api_key: Your API Key from ecal.com
ecal_api_secret: Your API Secret from ecal.com
ecal_calendar_id: Your Calendar ID from ecal.com
error_file_path: /app/errors.txt
```

## Installation

1. Clonez ce dépôt sur votre machine locale.
2. Placez-vous dans le répertoire du projet.
3. Créez et démarrez un conteneur à partir du fichier.
```
docker-compose up --build
```
4. Relancer le conteneur après exteiction
```
docker-compose up
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
 - `docker-compose.yml`: 
 - `config.yml`: Contient les configurations nécessaires.
 - `app/requirements.txt`: Liste des dépendances Python.
 - `app/cronjob`: Définit les tâches cron.
 - `app/agenda.py`: Script principal pour la synchronisation des événements.

## Auteurs
Ce projet a été réalisé par **SABOT DRESSY Nathan**.
