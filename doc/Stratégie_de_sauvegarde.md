# Stratégie de sauvegarde du serveur AOTF

## Quelles données sont à sauvegarder ?

La base de données d’AOTF est la seule donnée à sauvegarder. Mais le fichier `parameters.py` est aussi à conserver en sécurité afin de faciliter la restauration du serveur. Cependant, si vous ne pouvez pas le conserver en sureté (C'est à dire sans le chiffrer), il vaut mieux éviter de le sauvegarder, afin de limiter le risque de vol de vos clés, et notamment de vos `auth_token`, qui sont les plus sensibles.


## Comment sauvegarder la base de données MySQL d'AOTF ?

### Dump MySQL

Le **dump MySQL** est la méthode la plus simple pour sauvegarder une BDD MySQL. Elle peut cependant être très lente pour les grosses BDD sur un disque dur mécanique (HDD). Attention, il est impératif d'utiliser l'option `--hex-blob`, qui permet d'exporter proprement les données binaires (Empreintes des images). De plus, l'utilisation de l'option `--single-transaction` peut être intéressante afin de ne pas verrouiller les tables, permettant de ne pas avoir à éteindre le serveur AOTF.
```
MYSQL_PWD="motdepasse" mysqldump -u Artists_on_Twitter_Finder --hex-blob --single-transaction --no-tablespaces Artists_on_Twitter_Finder accounts tweets reindex_tweets > AOTF_$(date '+%Y-%m-%d').sql
```

Comme le serveur AOTF garantie à tout moment la cohérence des données dans sa base, il n'a pas besoin d'être éteint lors d'un dump. De plus, l'option `--single-transaction` permet de prendre un instantané de la base, et ainsi de conserver cette cohérence. Enfin, la table `accounts` est exportée avant les tables de Tweets, empêchant le dump de contenir un curseur d'indexation plus récent que les Tweets enregistrés (Et donc potentiellement des Tweets manquants).

Le script de maintenance [`mysqldump_backup.py`](../maintenance/mysqldump_backup.py) permet d'exécuter facilement dump MySQL de la base de données du serveur AOTF en utilisant les paramètres définis dans le fichier `parameters.py`. Il place les dumps dans le répertoire [`backups`](../backups). Ce script peut être exécuté en tant que tâche Cron, par exemple une fois par semaine.

La restauration peut se faire avec la commande suivante :
```
MYSQL_PWD="motdepasse" mysql -u Artists_on_Twitter_Finder Artists_on_Twitter_Finder < AOTF_YYYY-MM-DD.sql
```

Afin de vous faire une idée, voici des exemples de dumps MySQL réalisés (Serveur sur un disque SSD) :
* 90 Mo pour une BDD de 800k Tweets et 1300 comptes Twitter (S'est exécuté instantanément)
* 1 Go pour une BDD de 9,6 millions de Tweets et 12k comptes Twitter (S'est exécuté en quelques secondes)


### Réplication MySQL

La manière la plus efficace de sauvegarder la base de données est de faire de la **réplication MySQL**, ce qui nécessite un deuxième serveur MySQL. Ce deuxième serveur est appelé le serveur "esclave", et le serveur principal le serveur "maitre". Le serveur esclave se connecte avec un compte sur le serveur maitre **qui a uniquement des permissions de lecture**, et réplique chez lui les opérations réalisées (Grace aux journaux binaires).

Cependant, cette solution est une méthode de luxe, puisqu'elle nécessite un deuxième serveur. Si les dumps MySQL fonctionnent bien, vous n'avez pas besoin de faire de réplication (Sauf si vous souhaitez multiplier les sauvegardes).


### Copie de `/var/lib/mysql`

Une autre manière de sauvegarder la base de données est de **copier le répertoire où MySQL stocke les données**. Sous Linux, ce répertoire est généralement `/var/lib/mysql`. Vous pouvez sinon exécuter la requête `SELECT @@datadir;` pour le déterminer. Avertissement sur cette méthode :
1. Le serveur MySQL doit être éteint avant de faire toute opération (Copie ou restauration).
2. Tous les fichiers du répertoire de MySQL doivent être récursivement sauvegardés et restaurés.
3. Attention au propriétaire et aux permissions de fichiers, notamment lors de la restauration.
4. Toutes les bases de données du serveur seront sauvegardées, pas seulement celle d'AOTF.

Cependant, cette méthode est complexe par rapport aux dumps ou à la réplication. Elle doit être utilisée en dernier recours si les dumps MySQL sont beaucoup trop lents pour vous, et que n'avez pas de deuxième serveur MySQL pour faire de la réplication. Afin d'accélérer les dumps, et tout votre serveur, il est recommandé d'utiliser un disque dur SSD, ça change la vie.
