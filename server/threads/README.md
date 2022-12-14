# Procédures des threads du serveur AOTF

Le script `app.py` (Présent dans le répertoire parent à celui-ci), est le script central du serveur AOTF, et donc la racine de l'arbre des threads et processus fils (Si on est en mode multi-processus, c'est à dire que le paramètre `ENABLE_MULTIPROCESSING` est à `True`). Il gère ses threads et processus fils (Qui contiennent des threads), ainsi que celui de la mémoire partagée; via la classe `Threads_Manager` (Répertoire [`app`](../app)).

Les procédures des threads sont présentes dans ce répertoire, ainsi que les fonctions utilisées pour les démarrer.
Les objets de la mémoire partagée et sa procédure de thread sont présents dans le répertoire [`shared_memory`](../shared_memory).


## Rappel sur les requêtes traitées

Il y a deux types de requêtes : Les requêtes utilisateur, et les requêtes de scan. Elles sont gérées et traitées respectivement par les threads de traitement des répertoires [`user_pipeline`](user_pipeline) et [`scan_pipeline`](scan_pipeline). Les classes des requêtes sont présentes dans le répertoire [`shared_memory`](../shared_memory).


## Liste des procédures des threads

- Les threads de traitement des requêtes utilisateurs sont dans [`user_pipeline`](user_pipeline).
- Les threads de traitement des requêtes de scan sont dans [`scan_pipeline`](scan_pipeline).
- Le thread du serveur HTTP et sa classe sont dans [`http_server`](http_server).
- Les threads de maintenance sont dans [`maintenance`](maintenance).


## Procédures de démarrage des threads

La fonction `error_collector()` est le collecteur d'erreurs. C'est la procédure conteneur de chaque thread du serveur. Comme son nom l'indique, elle permet de collecter les erreurs, de les enregistrer dans des fichiers, et de redémarrer le thread. Elle met aussi la requête en échec si le thread était en train de traiter une requête (Utilisateur ou scan).

Les fonctions dans le script `threads_launchers.py` permettent de lancer des threads dans le collecteur d'erreurs :
- `launch_thread()` : Lancer un thread sans conteneur ou un thread seul dans un processus.
- `launch_identical_threads_in_container()` : Lancer plusieurs threads ou processus identiques, c'est à dire qu'ils utilisent la même procédure. Si ce sont des threads et que le mode multi-processus est activé (`ENABLE_MULTIPROCESSING` à `True`), ils seront placés dans processus conteneur. Cela permet de rendre leur GIL indépendant, sans prendre autant de mémoire vive si tous ces threads étaient des processus.
- `threads_container_for_unique_threads()` : Idem, mais pour des threads ou processus uniques.

Tous les threads ou processus fils du script `app.py` sont exécutés par une de ces trois fonctions. La seule exception est le thread du serveur de mémoire partagée Pyro, qui n'est pas exécuté dans le collecteur d'erreurs. Voir le répertoire [`shared_memory`](../shared_memory).

Ces fonctions sont utilisée dans le gestionnaire de threads, qui est la classe `Threads_Manager` (Répertoire [`app`](../app)). Celle-ci rassemble sans sa méthode `launch_threads()` tous les éléments de ce répertoire `threads`.

Note : Tout comme `app.py`, les processus fils peuvent gérer les signaux `SIGTERM`, `SIGINT` et `SIGHUP`.
