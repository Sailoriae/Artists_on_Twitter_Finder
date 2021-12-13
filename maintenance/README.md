# Artists on Twitter Finder : Scripts de maintenance

* Script [`remove_deleted_accounts.py`](remove_deleted_accounts.py) :
  Permet de supprimer les comptes de la base de données qui n'existent plus sur Twitter. Supprime aussi leurs Tweets.
  **Attention :** Ce script supprime les comptes supprimés, suspendus ou ajoutés sur la liste noire d'AOTF.
  Il ne supprime pas les comptes passés en privé. Et aucune idée de ce qu'il fait des comptes désactivés.

* Script [`cleanup_database.py`](cleanup_database.py) :
  Permet de vérifier que les Tweets enregistrés dans la base de données ont bien un compte enregistré correspondant.
  Puis supprime les Tweets sans compte enregistré (Et ainsi les empreintes des images de ces Tweets).

* Script [`mysqldump_backup.py`](mysqldump_backup.py) :
  Ce script permet de sauvegarder la base de données en faisant un Dump MySQL.
  Au passage, il supprime les anciennes sauvegardes qui ont plus de 6 semaines.
  La raison de ce script est qu'il va chercher tout seul les paramètres dans le fichier "parameters.py".
  Il peut ainsi être utilisé facilement en tant que tâche dans une table Cron.
  Les Dumps sont enregistrés dans le répertoire [`../backups`](../backups).


## Requêtes SQL utiles

Obtenir la liste des comptes ayant le plus de Tweets indexés.
```
SELECT account_id, COUNT(*) as indexed_tweets_count
FROM tweets
GROUP BY account_id
ORDER BY indexed_tweets_count DESC
```

Afficher un profil Twitter à partir de son ID (En remplaçant `123456` par l'ID, un nombre entier).
```
https://twitter.com/intent/user?user_id=123456
https://twitter.com/i/user/123456
```

Explorer les comptes ayant le plus de Tweets indexés. Cela peut être utile pour chercher des gros comptes qui ne sont pas des artistes, et ainsi mettre à jour la liste noire (Voir [`blacklist.py`](../server/tweet_finder/blacklist.py)).
```
SELECT CONCAT("https://twitter.com/i/user/", account_id) as account_url, COUNT(*) as indexed_tweets_count
FROM tweets
GROUP BY account_id
ORDER BY indexed_tweets_count DESC
```
