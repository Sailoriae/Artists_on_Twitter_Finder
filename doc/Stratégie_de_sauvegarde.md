# Stratégie de sauvegarde du serveur AOTF

## Quelles données sont à sauvegarder ?

La base de données d’AOTF est la seule donnée à sauvegarder. Mais le fichier `parameters.py` est aussi à conserver en sécurité afin de faciliter la restauration du serveur.

## Comment sauvegarder la base de données MySQL d'AOTF ?

### Dump MySQL

Le **dump MySQL** peut être intéressant pour des petites base de données, mais devient trop long et trop volumineux lorsque la base de données grandit. Attention, il est impératif d'utiliser l'option `--hex-blob`, qui permet d'exporter proprement les données binaires (Empreintes des images). De plus, l'utilisation de l'option `--single-transaction` peut être intéressante afin de ne pas vérouiller les tables, permettant de ne pas avoir à éteindre le serveur AOTF.
```
MYSQL_PWD="motdepasse" mysqldump -u Artists_on_Twitter_Finder --hex-blob --single-transaction --no-tablespaces Artists_on_Twitter_Finder accounts tweets reindex_tweets > AOTF_$(date '+%Y-%m-%d').sql
```
*(90 Mo pour une BDD de 800k Tweets et 1300 comptes Twitter)*

La restauration peut se faire avec la commande suivante :
```
MYSQL_PWD="motdepasse" mysql -u Artists_on_Twitter_Finder Artists_on_Twitter_Finder < AOTF_YYYY-MM-DD.sql
```

### Réplication MySQL

Ainsi, la manière la plus efficace de sauvegarder la base de données est de faire de la **réplication MySQL**, ce qui nécessite un deuxième serveur MySQL. Ce deuxième serveur est appelé le serveur "esclave", et le serveur principal le serveur "maitre". Le serveur esclave se connecte avec un compte sur le serveur maitre **qui a uniquement des permissions de lecture**, et réplique chez lui les opérations réalisées (Grace aux journaux binaires).

### Copie de `/var/lib/mysql`

Une autre manière de sauvegarder la base de données est de **copier le répertoire où MySQL stocke les données**. Sous Linux, ce répertoire est généralement `/var/lib/mysql`. Vous pouvez sinon éxécuter la requête `SELECT @@datadir;` pour le déterminer. Avertissement sur cette méthode :
1. Le serveur MySQL doit être éteint avant de faire toute opération (Copie ou restauration).
2. Tous les fichiers du répertoire de MySQL doivent être récursivement sauvegardés et restaurés.
3. Attention au propriétaire et aux permission de fichiers, notamment lors de la restauration.
4. Toutes les bases de données du serveur seront sauvegardées, pas seulement celle d'AOTF.
