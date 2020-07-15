# Module des dépendances du script `app.py`

Le script `app.py` (Présent dans le répertoire parent à celui-ci), est le script scentral de la partie serveur.
Il crée et gère les threads de traitement, la ligne de commande, les files d'attentes des requêtes, et le serveur HTTP.

Mais comme tout ceci faisait un script beaucoup trop long, il a été séparé en plusieurs fichiers, ici, dans le module `app`.


## Liste des procédures des threads

Voici la liste des procédure principales pour chaque thread (Ou plutôt "type de thread", puisqu'elles peuvent être utilisées plusieurs fois pour créer plusieurs fois le même thread) :
- `thread_step_1_link_finder` : Thread de traitement de la partie Link Finder : Chercher les comptes Twitter de l'artiste de l'illustration de requête.
- `thread_step_2_list_account_tweets` : Premier thread de traitement de la partie Tweet Finder : Listage des Tweets par GetOldTweets3.
- `thread_step_3_index_twitter_account` : Deuxième thread de traitement de la partie Tweet Finder : Indexation des Tweets trouvés par GetOldTweets3.
- `thread_step_4_reverse_search` : Troisième thread de traitement de la partie Tweet Finder : Recherche d'image inversée.


## Liste des classes

- `class_HTTP_Server` : Classe du serveur HTTP.
- `class_Threaded_HTTP_Server` : Classe du serveur HTTP pour le multi-thread.

- `class_Request` : Réprésentation d'une requête. Les requêtes sont identifiées par leur URL de requête.
- `class_Pipeline` : Mémoire partagée entre tous les threads. Contient l'ensemble des requêtes, les files d'attentes, et leur gestion.
