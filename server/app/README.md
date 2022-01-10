# Fonctions diverses pour `app.py`

Le script `app.py` (Présent dans le répertoire parent à celui-ci), est le script central du serveur AOTF.
Il initialise la mémoire partagée, démarre les threads (Ou processus si le paramètre `ENABLE_MULTIPROCESSING` est à `True`), et éxécute la ligne de commande.

Les procédures des threads et les fonctions utilisées pour les démarrer sont présentes dans le répertoire [`threads`](../threads).
Les objets de la mémoire partagée sont présents dans le répertoire [`shared_memory`](../shared_memory).

Diverses fonctions utilisée par ce script sont ici présentes :

- `check_parameters()` : Fonction permettant de vérifier les données dans `parameters.py`. Exécutée au démarrage du serveur AOTF.
