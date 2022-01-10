# Stratégie de sauvegarde du serveur AOTF

## Quelles données sont à sauvegarder ?

La base de données d’AOTF est la seule donnée à sauvegarder. Mais le fichier `parameters.py` est aussi à conserver en sécurité afin de faciliter la restauration du serveur.


## Comment sauvegarder la base de données MySQL d'AOTF ?

### Dump MySQL

Le **dump MySQL** peut être intéressant pour des petites bases de données, mais peut devenir trop long et trop volumineux lorsque la base de données grandit. Attention, il est impératif d'utiliser l'option `--hex-blob`, qui permet d'exporter proprement les données binaires (Empreintes des images). De plus, l'utilisation de l'option `--single-transaction` peut être intéressante afin de ne pas verrouiller les tables, permettant de ne pas avoir à éteindre le serveur AOTF.
```
MYSQL_PWD="motdepasse" mysqldump -u Artists_on_Twitter_Finder --hex-blob --single-transaction --no-tablespaces Artists_on_Twitter_Finder accounts tweets reindex_tweets > AOTF_$(date '+%Y-%m-%d').sql
```

Comme le serveur AOTF garantie à tout moment la cohérence des données dans sa base, il n'a pas besoin d'être éteint lors d'un dump.

Le script de maintenance [`mysqldump_backup.py`](../maintenance/mysqldump_backup.py) permet d'exécuter facilement dump MySQL de la base de données du serveur AOTF en utilisant les paramètres définis dans le fichier `parameters.py`. Il place les dumps dans le répertoire [`backups`](../backups). Ce script peut être exécuté en tant que tâche Cron, par exemple une fois par semaine.

La restauration peut se faire avec la commande suivante :
```
MYSQL_PWD="motdepasse" mysql -u Artists_on_Twitter_Finder Artists_on_Twitter_Finder < AOTF_YYYY-MM-DD.sql
```

Afin de vous faire une idée, voici des exemples de dumps MySQL réalisés :
* 90 Mo pour une BDD de 800k Tweets et 1300 comptes Twitter (S'est exécuté instantanément)
* 1 Go pour une BDD de 9,6 millions de Tweets et 12k comptes Twitter (S'est exécuté en quelques secondes)


### Réplication MySQL

La manière la plus efficace de sauvegarder la base de données est de faire de la **réplication MySQL**, ce qui nécessite un deuxième serveur MySQL. Ce deuxième serveur est appelé le serveur "esclave", et le serveur principal le serveur "maitre". Le serveur esclave se connecte avec un compte sur le serveur maitre **qui a uniquement des permissions de lecture**, et réplique chez lui les opérations réalisées (Grace aux journaux binaires).


### Copie de `/var/lib/mysql`

Une autre manière de sauvegarder la base de données est de **copier le répertoire où MySQL stocke les données**. Sous Linux, ce répertoire est généralement `/var/lib/mysql`. Vous pouvez sinon exécuter la requête `SELECT @@datadir;` pour le déterminer. Avertissement sur cette méthode :
1. Le serveur MySQL doit être éteint avant de faire toute opération (Copie ou restauration).
2. Tous les fichiers du répertoire de MySQL doivent être récursivement sauvegardés et restaurés.
3. Attention au propriétaire et aux permission de fichiers, notamment lors de la restauration.
4. Toutes les bases de données du serveur seront sauvegardées, pas seulement celle d'AOTF.
