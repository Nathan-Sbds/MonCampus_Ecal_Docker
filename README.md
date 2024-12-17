# MonCampus_Ecal_Docker

Ce projet configure un conteneur Docker pour synchroniser les événements entre MonCampus et l'API ecal.com. Il utilise Python et plusieurs dépendances pour récupérer, formater et synchroniser les événements efficacement.

---

## Prérequis

- Docker installé sur votre machine (voir la documentation officielle de Docker : https://docs.docker.com/get-docker/).
- Clé API et informations de connexion pour ecal.com.
- Identifiants pour accéder à MonCampus.

---

## Tutoriel : Récupérer vos Clés API et l'Identifiant de votre Calendrier sur ecal.com

Pour intégrer les services d'ECAL à votre application MonCampus, il est essentiel d'obtenir votre clé API, votre clé secrète et l'identifiant de votre calendrier. 

<details>
  <summary>Cliquez ici pour ouvrir le guide détaillé.</summary>

### Étape 1 : Créer un Compte sur ecal.com
1. **Accédez au site officiel d'ECAL** : Rendez-vous sur [ecal.com](https://ecal.com).
2. **Inscription** : Cliquez sur `Start Free Trial` ou `Login` si vous avez déjà un compte.
3. **Complétez l'inscription** : Fournissez les informations requises pour créer votre compte.

### Étape 2 : Accéder à la Section Développeur
1. **Connexion** : Connectez-vous à votre compte ECAL.
2. **Accédez à la section Développeur** : Dans le tableau de bord, naviguez vers `Developers` puis `API Keys`.

### Étape 3 : Récupérer votre Clé API et Clé Secrète
1. **Clé API** : Une clé est créée par défaut. La colonne `Key` vous permettra de récupérer la clé API.
2. **Clé Secrète** : Le cadenas présent à côté de la clé API vous permettra de récupérer la clé secrète. Cette étape est primordiale.

### Étape 4 : Créer un Calendrier
1. **Accéder à la Section Calendrier** : Dans le tableau de bord, naviguez vers `Schedules & Events` puis `Add Schedule`.
2. **Créer un Calendrier** : Sélectionnez `Manual Entry` puis fournissez les informations requises pour créer votre calendrier.

### Étape 5 : Récupérer l'Identifiant du Calendrier
1. **Gérer les Événements** : Cliquez sur la roue dentée de réglages nommée `Manage Events`.
2. **Identifier l'Identifiant** : L'identifiant se trouve dans le fil d'Ariane en haut de l'écran, entre `Schedules` et `Events`. Il est composé de 24 caractères au format hexadécimal.

### Étape 6 : Insérer les Informations dans `config.yml`
Après avoir récupéré ces éléments, vous pouvez les insérer dans votre fichier `config.yml` pour configurer votre application.

### Étape 7 : Mettre le Calendrier en Ligne
1. **Gérer les Calendriers** : Dans le tableau de bord, naviguez vers `Schedules & Events` puis `Manage Schedules`.
2. **Mettre en Ligne** : Sélectionnez le calendrier nouvellement créé puis cliquez sur le bouton vert nommé `Set Live`.

### Étape 8 : Récupérer le Lien du Calendrier
1. **Ajouter un Display** : Dans le tableau de bord, naviguez vers `Displays` puis `Add Display`.
2. **Configurer le Display** : Sélectionnez `Button Display` puis fournissez les informations requises pour créer votre calendrier. Le Display ID peut être une valeur aléatoire.
3. **Associer le Calendrier** : Dans l'onglet `Schedules`, choisissez `Only show these Schedules` et sélectionnez le calendrier à partager. Il est recommandé de sélectionner `Enable Auto-subscribe`.
4. **Options** : Dans l'onglet `Options`, vous pouvez modifier diverses options. Il est recommandé de désactiver `Welcome Message` et `Sharing`, mais cela n'est pas obligatoire.
5. **Enregistrer** : Cliquez sur le bouton `Save`.
6. **Mettre en Ligne** : Sélectionnez le bouton nouvellement créé puis cliquez sur le bouton vert nommé `Set Live`.
7. **Obtenir le Lien** : Un lien est disponible en cliquant sur l'icône `<>` nommée `Button Code` dans l'onglet `App`.
8. **QR Code** : Un QR Code est également disponible depuis l'icône correspondante nommée `View Button QR Code`.

Vous êtes maintenant prêt à partager et utiliser votre calendrier. Il est désormais possible de s'y abonner depuis n'importe quel appareil compatible.

</details>

Pour des informations détaillées sur l'utilisation de l'API d'ECAL, consultez la [documentation officielle](https://docs.ecal.com/reference/apiv2.html).

---

## Configuration

Avant de démarrer, configurez le fichier `config.yml` avec vos informations personnelles et les clés API nécessaires :  

```yaml
[CONFIG]
moncampus_username: Votre nom d'utilisateur MonCampus  
moncampus_password: Votre mot de passe MonCampus  
moncampus_start_date: Date de début (AAAA-MM-JJ) pour récupérer les événements MonCampus  
moncampus_end_date: Date de fin (AAAA-MM-JJ) pour récupérer les événements MonCampus  
ecal_api_key: Votre clé API ecal.com  
ecal_api_secret: Votre clé secrète API ecal.com  
ecal_calendar_id: L'ID de votre calendrier sur ecal.com  
error_file_path: /app/errors.txt  # Ne pas modifier cette valeur si vous ne savez pas ce que vous faites  
```

---

## Installation

1. Clonez ce dépôt :  
```bash
git clone https://github.com/Nathan-Sbds/MonCampus_Ecal_Docker 
cd MonCampus_Ecal_Docker 
``` 

2. Construisez et démarrez le conteneur :  
```bash
docker compose up --build  
```
3. Pour relancer le conteneur après extinction :  
```bash
docker compose up  
```

---

## Utilisation

Une fois le conteneur démarré, un service cron est activé pour exécuter automatiquement le script de synchronisation à des intervalles réguliers. Ces intervalles sont définis dans le fichier `app/cronjob`.

Vous pouvez également exécuter manuellement le script principal depuis le conteneur pour tester et/ou initialiser les premiers évenements (recommandé en cas de premier lancement) :  
```bash
docker exec -it moncampusecal python /app/agenda.py  
```

---

## Démarrage automatique sur Linux (Debian/Raspberry Pi)

Si vous utilisez un système basé sur Debian ou un Raspberry Pi, vous pouvez configurer le démarrage automatique de vos conteneurs Docker avec une tâche cron (accessible avec `crontab -e`) comme suit :  

```bash
@reboot /bin/bash -c "cd ~/MonCampus_Ecal_Docker && sudo docker compose up -d >> /var/log/cron.log 2>&1"
```

### Vérification

Après le redémarrage de la machine, utilisez la commande suivante pour vérifier si les deux conteneurs sont bien lancés :  
```bash
docker ps
```
Cette commande liste tous les conteneurs en cours d'exécution. Vous devriez voir vos deux conteneurs dans la liste.  

Si l'un des deux conteneurs ne s'est pas lancé, vérifiez les journaux :  
- `/var/log/cron.log`

Assurez-vous que :  
- Votre utilisateur dispose des permissions nécessaires pour exécuter Docker.  
- La commande `docker compose` est correctement configurée sur votre système (ou utilisez `docker-compose` si vous avez une version plus ancienne).  

---

## Fonctionnalités

1. Récupération des événements :
   Connexion à MonCampus pour récupérer les événements dans la plage de dates spécifiée.  

2. Formatage des événements :
   Transformation des données récupérées pour qu'elles soient compatibles avec l'API ecal.com.  

3. Synchronisation des événements :
   Envoi des événements formatés à l'API ecal.com pour mise à jour dans le calendrier.  

4. Suppression des doublons :
   Vérification et suppression automatique des doublons dans le calendrier ecal.com.  

5. Vérification de la cohérence :
   Comparaison du nombre d'événements entre MonCampus et ecal.com pour s'assurer de la synchronisation complète.  

---

## Dépendances

Les dépendances Python nécessaires sont listées dans `requirements.txt`. Elles sont automatiquement installées lors de la construction de l'image Docker. Voici les principales bibliothèques utilisées :  

- `requests` : Pour les appels API.  
- `python-crontab` : Pour la gestion des tâches cron.  
- `pytz` : Pour la gestion des fuseaux horaires.  
- `pyyaml` : Pour la lecture des fichiers YAML.  

---

## Structure du Projet

| Fichier/Dossier | Description |
|---------------- | -----------   |
| `Dockerfile` | Définit les instructions pour construire l'image Docker.   |
| `docker-compose.yml` | Gère le conteneur et ses services associés.   |
| `config.yml` | Contient les configurations nécessaires pour MonCampus et ecal.com.   |
| `app/requirements.txt` | Liste des dépendances Python.   |
| `app/cronjob` | Définit les tâches cron pour l'exécution automatique du script. | 
| `app/agenda.py` | Script principal pour la synchronisation des événements.   |
| `app/errors.txt` | Fichier de log des erreurs (généré automatiquement en cas de problème).   |

---

## Débogage et Logs

En cas de problème, consultez les logs Docker avec :  
```bash
docker logs moncampusecal
```

Les erreurs spécifiques liées à la synchronisation sont enregistrées dans :  
```bash
/app/errors.txt  
```

---

## Améliorations Futures

- Ajout d'une interface utilisateur pour une gestion simplifiée.  
- Notifications par e-mail en cas d'erreurs critiques.  
- Optimisation des performances pour des synchronisations massives.  
- Tests unitaires pour une meilleure robustesse.  

---

## Contribution

Les contributions sont les bienvenues !  
1. Forkez le projet.  
2. Créez une branche pour vos modifications :  
```bash
   git checkout -b ma-nouvelle-fonctionnalite  
```
3. Poussez vos modifications et soumettez une pull request.  

---

## Auteurs

Ce projet a été réalisé par :  
**Nathan SABOT DRESSY**

---

## Licence

Ce projet est sous licence MIT. Vous êtes libre de l'utiliser et de le modifier, à condition de conserver la mention de l'auteur original.  
