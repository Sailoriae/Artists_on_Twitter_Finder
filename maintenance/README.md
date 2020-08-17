# Artist on Twitter Finder : Scripts de maintenance

## Script `remove_deleted_accounts.py`

Permet de supprimer les comptes de la base de données qui n'existent plus sur Twitter. Supprime aussi leurs Tweets.

Attention : Ce script supprime les comptes supprimés, suspendus ou passés en privé / protégé.


## Script `extract_tweets_ids_from_error_file.py`

Permet d'extraire les indexation de Tweets qui ont échoué (Fichier `class_CBIR_Engine_with_Database_errors.log`) et de retenter de les indexer.


## Requêtes SQL diverses

Extraire les ID de comptes Twitter qui n'ont pas d'enregistrement dans la table `accounts` :

```
SELECT DISTINCT tweets.account_id
FROM tweets
LEFT JOIN accounts ON tweets.account_id = accounts.account_id
WHERE accounts.account_id IS NULL
```

Extraire les Tweets qui sont enregistrés dans la table `tweets`, mais n'ont aucune image enregistrée dans les 4 tables d'images :

```
SELECT tweet_id FROM tweets WHERE
NOT EXISTS ( SELECT tweets_images_1.tweet_id FROM tweets_images_1 WHERE tweets_images_1.tweet_id = tweets.tweet_id ) AND
NOT EXISTS ( SELECT tweets_images_2.tweet_id FROM tweets_images_2 WHERE tweets_images_2.tweet_id = tweets.tweet_id ) AND
NOT EXISTS ( SELECT tweets_images_3.tweet_id FROM tweets_images_3 WHERE tweets_images_3.tweet_id = tweets.tweet_id ) AND
NOT EXISTS ( SELECT tweets_images_4.tweet_id FROM tweets_images_4 WHERE tweets_images_4.tweet_id = tweets.tweet_id )
```
