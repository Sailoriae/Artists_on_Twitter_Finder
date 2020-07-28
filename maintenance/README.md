# Artist on Twitter Finder : Scripts de maintenance

## `remove_deleted_accounts.py`

Permet de supprimer les comptes de la base de données qui n'existent plus sur Twitter. Supprime aussi leurs Tweets.

Les comptes privés, suspendus, ou désactivés, ne sont pas supprimés !


## `extract_tweets_ids_from_error_file.py`

Permet d'extraire les indexation de Tweets qui ont échoué (Fichier `class_CBIR_Engine_with_Database_errors.log`) et de retenter de les indexer.
