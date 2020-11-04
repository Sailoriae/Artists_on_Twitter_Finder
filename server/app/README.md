# Module des dépendances du script `app.py`

Le script `app.py` (Présent dans le répertoire parent à celui-ci), est le script central de la partie serveur.
Il crée et gère les threads de traitement, la ligne de commande, les files d'attentes des requêtes, et le serveur HTTP.

Mais comme tout ceci faisait un script beaucoup trop long, il a été séparé en plusieurs fichiers, ici, dans le module `app`.


## Requêtes

Il y a deux types de requêtes : Les requêtes utilisateur, et les requêtes de scan. Elles sont gérées et traitées respectivement dans les sous-modules `user_pipeline` et `scan_pipeline`.


## Liste des procédures des threads

Les threads de traitement sont dans le sous-module `user_pipeline` et `scan_pipeline`. A ces threads s'ajoutent les suivants :

- `thread_http_server` : Thread de serveur HTTP.
- `thread_auto_update_accounts` : Thread de mise à jour automatique des comptes dans la base de données.
- `thread_remove_finished_requests` : Thread de délestage des requêtes terminées. Les requêtes utilisateurs sont conservées 1h, et les requêtes de scan 24h.
- `thread_reset_SearchAPI_cursors` : Thread de suppression des curseurs d'indexation avec l'API de recherche, car l'indexation sur le moteur de recherche de Twitter est très fluctuante.

- `error_collector` : Procédure conteneuse de chaque thread du serveur (Exécute les procédures ci-dessus). Permet de collecter les erreurs, de les enregistrer dans des fichiers, et de redémarrer le thread. Elle met aussi la requête en échec si le thread était en train de traiter une requête.


## Liste des classes

- `class_HTTP_Server` : Classe du serveur HTTP. Le serveur HTTP intégré contient uniquement l'API.
- `class_Threaded_HTTP_Server` : Classe du serveur HTTP pour le multi-thread.
