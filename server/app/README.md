# Dépendances directes de `app.py`

Le script `app.py` (Présent dans le répertoire parent à celui-ci), est le script central du serveur AOTF.
Il initialise la mémoire partagée, démarre les threads (Qui peuvent être dans des processus conteneurs si le paramètre `ENABLE_MULTIPROCESSING` est à `True`), et exécute la ligne de commande.

Les procédures des threads et les fonctions utilisées pour les démarrer sont présentes dans le répertoire [`threads`](../threads).
Les objets de la mémoire partagée et la fonction utilisée pour la démarrer sont présents dans le répertoire [`shared_memory`](../shared_memory).

Avant de démarrer les threads, le serveur vérifie les données dans `parameters.py` via la fonction `check_parameters()`.

La classe `Threads_Manager` est la classe centrale du script `app.py`. Lorsqu'elle est instanciée, elle est le gestionnaire des threads du serveur AOTF (Dont le thread du serveur de mémoire partagée si on est en mode multi-processus). Ce gestionnaire permet de démarrer les threads, de les arrêter, et de gérer les signaux demandant l'arrêt du serveur (`SIGTERM`, `SIGINT` et `SIGHUP`).

Elle utilise deux autres éléments :
- `Debug_File` : Classe du fichier de débug. Ne fait rien si le paramètre `DEBUG` est sur `False`.
- `define_max_file_descriptors()` : Fonction permettant d'augmenter le nombre maximal de descripteurs de fichiers.

Enfin, la classe `Command_Line_Interface` contient l'entrée ligne de commande (CLI) et l'éxécution des commandes. Une fois instanciée, sa boucle infinie peut être exécutée via sa méthode `do_cli_loop()`.
