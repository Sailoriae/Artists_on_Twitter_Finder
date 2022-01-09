# Module des threads du serveur (Dépendances du script `app.py`)

Le script `app.py` (Présent dans le répertoire parent à celui-ci), est le script central du serveur AOTF.
Il initialise la mémoire partagée, démarre les threads (Ou processus si le paramètre `ENABLE_MULTIPROCESSING` est à `True`), et éxécute la ligne de commande.
Les procédures des threads sont présentes dans ce module, ainsi que les fonctions utilisées pour les démarrer.


## Rappel sur les requêtes traitées

Il y a deux types de requêtes : Les requêtes utilisateur, et les requêtes de scan. Elles sont gérées et traitées respectivement par les threads de traitement des sous-modules [`user_pipeline`](user_pipeline) et [`scan_pipeline`](scan_pipeline). Les classes des requêtes sont présentes dans le module [`../shared_memory`](../shared_memory).


## Liste des procédures des threads

- Les threads de traitement des requêtes utilisateurs sont dans [`user_pipeline`](user_pipeline).
- Les threads de traitement des requêtes de scan sont dans [`scan_pipeline`](scan_pipeline).
- Le thread du serveur HTTP et sa classe sont dans [`http_server`](http_server).
- Les threads de maintenance sont dans [`maintenance`](maintenance).


## Procédures de démarrage des threads

La fonction `error_collector()` est le collecteur d'erreurs. C'est la procédure conteneuse de chaque thread du serveur. Comme son nom l'indique, elle permet de collecter les erreurs, de les enregistrer dans des fichiers, et de redémarrer le thread. Elle met aussi la requête en échec si le thread était en train de traiter une requête (Utilisateur ou scan).

Les fonctions dans le script `threads_launchers.py` permettent de lancer les threads dans le collecteur d'erreurs :
- `launch_thread()` : Lancer un thread ou un processus sans conteneur.
- `launch_identical_threads_in_container()` : Lancer plusieurs threads ou processus identiques, c'est à dire qu'ils utilisent la même procédure. Si ce sont des threads et que `ENABLE_MULTIPROCESSING` est activé, ils seront placés dans processus conteneur. Cela permet de rendre leur GIL indépendant, sans prendre autant de mémoire vive si tous ces threads étaient des processus.
- `threads_container_for_unique_threads()` : Idem, mais pour des threads ou processus uniques.

Tous les threads ou processus fils du script `app.py` sont exécutés par une de ces trois fonctions. La seule exception est le thread du serveur Pyro, qui n'est pas exécuté dans le collecteur d'erreurs.

Tout comme `app.py`, les processus fils peuvent gérer les signaux `SIGTERM`, `SIGINT` et `SIGHUP`.


## Fonctions diverses

- `check_parameters()` : Fonction permettant de vérifier les données dans `parameters.py`. Exécutée au démarrage du serveur AOTF.
- `wait_until()` : Fonction utilisée par les threads de maintenance. Elle permet d'attendre jusqu'à un instant précis. Utilisée par les threads de maintenance.
