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
- `thread_remove_finished_requests` : Thread de délestage des requêtes terminées. Les requêtes utilisateurs sont conservées 3h (Ou 1h si elle s'est terminée en erreur, ou 10mins si elle s'est terminée en erreur d'entrée utilisateur), et les requêtes de scan 24h.
- `thread_reset_SearchAPI_cursors` : Thread de suppression des curseurs d'indexation avec l'API de recherche, car l'indexation sur le moteur de recherche de Twitter est très fluctuante.

- `error_collector` : Procédure conteneuse de chaque thread du serveur (Exécute les procédures ci-dessus). Permet de collecter les erreurs, de les enregistrer dans des fichiers, et de redémarrer le thread. Elle met aussi la requête en échec si le thread était en train de traiter une requête.


Les fonctions dans le script `threads_launchers.py` permettent de lancer les threads dans le collecteur d'erreurs :

- `launch_thread()` : Lancer un thread ou un processus sans conteneur.
- `launch_identical_threads_in_container()` : Lancer plusieurs threads ou processus identiques, c'est à dire qu'ils utilisent la même procédure. Si ce sont des threads et que `ENABLE_MULTIPROCESSING` est activé, ils seront placés dans processus conteneur. Cela permet de rendre leur GIL indépendant, sans prendre autant de mémoire vive si tous ces threads étaient des processus.
- `threads_container_for_unique_threads()` : Idem, mais pour des threads ou processus uniques.

Tous les threads ou processus fils du script `app.py` sont éxécutés par une de ces trois fonctions. La seule exception est le thread du serveur Pyro, qui n'est pas éxécuté dans le collecteur d'erreurs.


## Liste des classes

- `class_HTTP_Server` : Classe du serveur HTTP. Le serveur HTTP intégré contient uniquement l'API.
- `class_Threaded_HTTP_Server` : Classe du serveur HTTP pour le multi-thread.
