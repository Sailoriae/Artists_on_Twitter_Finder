# Dépendances directes de `app.py`

Le script `app.py` (Présent dans le répertoire parent à celui-ci), est le script central du serveur AOTF.
Il initialise la mémoire partagée, démarre les threads (Ou processus si le paramètre `ENABLE_MULTIPROCESSING` est à `True`), et exécute la ligne de commande.

Les procédures des threads et les fonctions utilisées pour les démarrer sont présentes dans le répertoire [`threads`](../threads).
Les objets de la mémoire partagée et la fonction utilisée pour la démarrer sont présents dans le répertoire [`shared_memory`](../shared_memory).

Divers éléments utilisés par ce script sont ici présents :
- `check_parameters()` : Fonction permettant de vérifier les données dans `parameters.py`. Exécutée au démarrage du serveur AOTF.
- `Command_Line_Interface` : Classe de la ligne de commande. Une fois instanciée, sa boucle infinie peut être exécutée via sa méthode `do_cli_loop()`.
- `Debug_File` : Classe du fichier de débug. Ne fait rien si le paramètre `DEBUG` est sur `False`.
