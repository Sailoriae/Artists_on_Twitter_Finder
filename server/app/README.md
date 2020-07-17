# Module des dépendances du script `app.py`

Le script `app.py` (Présent dans le répertoire parent à celui-ci), est le script scentral de la partie serveur.
Il crée et gère les threads de traitement, la ligne de commande, les files d'attentes des requêtes, et le serveur HTTP.

Mais comme tout ceci faisait un script beaucoup trop long, il a été séparé en plusieurs fichiers, ici, dans le module `app`.


## Liste des procédures des threads

Voici la liste des procédure principales pour chaque thread (Ou plutôt "type de thread", puisqu'elles peuvent être utilisées plusieurs fois pour créer plusieurs fois le même thread) :
- `thread_step_1_link_finder` : Thread de traitement de la partie Link Finder : Chercher les comptes Twitter de l'artiste de l'illustration de requête.
- `thread_step_2_GOT3_list_account_tweets` : Premier thread de traitement de la partie Tweet Finder : Listage des Tweets par GetOldTweets3.
- `thread_step_3_GOT3_index_account_tweets` : Deuxième thread de traitement de la partie Tweet Finder : Indexation des Tweets trouvés par GetOldTweets3.
- `thread_step_4_TwitterAPI_index_account_tweets` : Deuxième thread de traitement de la partie Tweet Finder : Indexation des Tweets par Tweepy sur l'API Twitter publique.
- `thread_step_5_reverse_search` : Troisième thread de traitement de la partie Tweet Finder : Recherche d'image inversée.

- `thread_http_server` : Thread de serveur HTTP.
- `thread_auto_update_accounts` : Thread de mise à jour automatique des comptes dans la base de données.
- `thread_remove_finished_requests` : Thread de délestage des requêtes terminées. Elles sont conservées 24h.

- `error_collector` : Procédure conteneuse de chaque thread du serveur (Exécute les procédures ci-dessus). Permet de collecter les erreurs, de les enregistrer dans des fichiers, et de redémarrer le thread. Elle met aussi la requête en échec si le thread était en train de traiter une requête.


## Liste des classes

- `class_HTTP_Server` : Classe du serveur HTTP. Le serveur HTTP intégré contient uniquement l'API.
- `class_Threaded_HTTP_Server` : Classe du serveur HTTP pour le multi-thread.

- `class_Request` : Réprésentation d'une requête. Les requêtes sont identifiées par leur URL de requête. L'objet Pipeline crée et gère toutes les requêtes.
- `class_Pipeline` : Mémoire partagée entre tous les threads. Contient l'ensemble des requêtes, les files d'attentes, et leur gestion.
