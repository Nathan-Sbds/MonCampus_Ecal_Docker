# MonCampus_Ecal_Docker

🚀 **Système Multi-Configurations Dynamique** - Synchronisez automatiquement vos événements MonCampus vers plusieurs calendriers ECAL simultanément.

## ✨ Fonctionnalités

- **Plusieurs configurations simultanées** : Gérez plusieurs emplois du temps avec différents calendriers ECAL
- **Gestion automatique** : Script unifié `manage.sh` qui génère automatiquement les services Docker
- **Déploiement flexible** : Démarrez toutes les instances ou une instance spécifique
- **Configuration simple** : Interface en ligne de commande pour ajouter facilement de nouvelles configurations

---

## 📋 Prérequis

- Docker et docker-compose installés ([Guide d'installation](https://docs.docker.com/get-docker/))
- Clés API et informations de connexion pour ecal.com
- Identifiants MonCampus

---

## � Démarrage Rapide

### 1. Cloner et accéder au projet
```bash
git clone <url-du-repo>
cd MonCampus_Ecal_Docker
```

### 2. Ajouter votre première configuration
```bash
./manage.sh add-config
```
*Suivez le guide interactif pour saisir vos informations MonCampus et ECAL*

### 3. Générer les services Docker
```bash
./manage.sh generate-compose
```
*Cette commande génère automatiquement le docker-compose.yml basé sur vos configurations*

### 4. Construire et démarrer
```bash
./manage.sh build
./manage.sh start
```

### 5. Vérifier le fonctionnement
```bash
./manage.sh status
./manage.sh logs config1  # Voir les logs de votre première config
```

**C'est tout !** Vos événements MonCampus sont maintenant synchronisés automatiquement vers ECAL.

---

## � Workflow Complet

### Ajouter plusieurs configurations
```bash
# Ajouter une config pour le campus principal
./manage.sh add-config

# Ajouter une config pour un autre campus
./manage.sh add-config

# Lister toutes vos configurations
./manage.sh config
```

### Gérer vos services
```bash
# Générer le docker-compose.yml (après ajout de nouvelles configs)
./manage.sh generate-compose

# Construire les images (requis après ajout de configs)
./manage.sh build

# Démarrer tous les services
./manage.sh start

# Démarrer un service spécifique
./manage.sh start config2

# Voir le statut de tous les services
./manage.sh status

# Voir les logs d'un service
./manage.sh logs config1

# Arrêter tous les services
./manage.sh stop

# Redémarrer un service spécifique
./manage.sh restart config2
```

---

## �️ Commandes du Script `manage.sh`

| Commande | Description | Exemple |
|----------|-------------|---------|
| `add-config` | **Ajouter une nouvelle configuration** | `./manage.sh add-config` |
| `build` | Construire les images Docker | `./manage.sh build` |
| `start [config]` | Démarrer les services | `./manage.sh start config1` |
| `stop [config]` | Arrêter les services | `./manage.sh stop` |
| `restart [config]` | Redémarrer les services | `./manage.sh restart config1` |
| `logs [config]` | Voir les logs | `./manage.sh logs config1` |
| `status` | Voir le statut des services | `./manage.sh status` |
| `config` | Lister les configurations | `./manage.sh config` |
| `generate-compose` | Régénérer docker-compose.yml | `./manage.sh generate-compose` |
| `clean` | Nettoyer containers et images | `./manage.sh clean` |
| `help` | Afficher l'aide | `./manage.sh help` |

---

## 🏗️ Structure du Projet

```
MonCampus_Ecal_Docker/
├── manage.sh                  # Script de gestion principal
├── generate-compose.sh        # Génération automatique docker-compose
├── docker-compose.yml         # Généré automatiquement
├── Dockerfile                # Image Docker
├── config.yml                # Configuration template
├── configs/                  # Vos configurations
│   ├── config1.yml          # Configuration 1
│   ├── config2.yml          # Configuration 2
│   └── ...
└── app/
    ├── agenda.py             # Script de synchronisation
    ├── requirements.txt      # Dépendances Python
    └── setup_cronjobs.sh    # Configuration cron
```

---

## 🔧 Configuration ECAL

<details>
<summary>📘 Guide complet : Obtenir vos clés API et calendrier ECAL</summary>

### 1. Créer un compte ECAL
- Accédez à [ecal.com](https://ecal.com)
- Cliquez sur `Start Free Trial` ou connectez-vous

### 2. Récupérer vos clés API
- Tableau de bord → `Developers` → `API Keys`
- **Clé API** : Colonne `Key`
- **Clé Secrète** : Cliquez sur le cadenas 🔒

### 3. Créer et configurer un calendrier
- `Schedules & Events` → `Add Schedule` → `Manual Entry`
- Remplissez les informations requises
- **Important** : Ajoutez au moins un événement temporaire

### 4. Récupérer l'ID du calendrier
- Cliquez sur ⚙️ `Manage Events`
- L'ID apparaît dans le fil d'Ariane (24 caractères hexadécimaux)

### 5. Mettre le calendrier en ligne
- `Schedules & Events` → `Manage Schedules`
- Sélectionnez votre calendrier → Bouton vert `Set Live`

Pour plus de détails, consultez la [documentation ECAL](https://docs.ecal.com/reference/apiv2.html).

</details>

---

## ⚠️ Résolution de Problèmes

### Vérifier les logs
```bash
# Logs d'un service spécifique
./manage.sh logs config1

# Logs Docker complets
docker logs moncampus-ecal-config1
```

### Problèmes courants

**Service ne démarre pas**
```bash
# Vérifier les erreurs de configuration
./manage.sh status
./manage.sh logs config1
```

**docker-compose.yml obsolète**
```bash
# Régénérer le fichier
./manage.sh generate-compose
./manage.sh build
```

**Erreurs de synchronisation**
- Vérifiez vos identifiants MonCampus
- Vérifiez vos clés API ECAL
- Consultez le fichier `/app/errors_configX.txt` dans le container

---

## 🔄 Automatisation et Démarrage au Boot

### Sur Linux (Raspberry Pi, Debian, Ubuntu)
Ajoutez cette ligne à votre crontab (`crontab -e`) :
```bash
@reboot /bin/bash -c "cd ~/MonCampus_Ecal_Docker && ./manage.sh start >> /var/log/moncampus.log 2>&1"
```

### Vérification après redémarrage
```bash
./manage.sh status
docker ps  # Vérifier que les conteneurs sont actifs
```

---

## 🔧 Fonctionnalités Techniques

1. **Récupération automatique** : Connexion à MonCampus pour récupérer les événements
2. **Formatage intelligent** : Transformation des données pour l'API ECAL
3. **Synchronisation bidirectionnelle** : Mise à jour complète du calendrier ECAL
4. **Suppression des doublons** : Évite les événements en double
5. **Vérification de cohérence** : S'assure que tous les événements sont synchronisés
6. **Exécution automatique** : Cron jobs pour maintenir la synchronisation

---

## 👥 Contribution

Les contributions sont bienvenues !

1. Forkez le projet
2. Créez votre branche : `git checkout -b ma-nouvelle-fonctionnalite`
3. Committez vos changements : `git commit -am 'Ajoute une nouvelle fonctionnalité'`
4. Poussez vers la branche : `git push origin ma-nouvelle-fonctionnalite`
5. Créez une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT. Vous êtes libre de l'utiliser et de le modifier.

**Auteur** : Nathan SABOT DRESSY  
