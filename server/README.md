# Serveur Artists on Twitter Finder

Le serveur de "Artists on Twitter Finder" exécute tout le traitement des requêtes, et gère sa base de données.
Il possède une API HTTP pour recevoir les requêtes, et y répondre (Lire sa documentation dans [`API_HTTP.md`](../doc/API_HTTP.md)).
Lorsqu'il est démarré, il affiche une interface en ligne de commande. Tapez `help` dans cette interface pour avoir la liste des commandes disponibles.


## Installation

0. Clonez ce dépôt (`git clone`), cela facilitera sa mise à jour (`git pull`). La branche pricipale contient toujours la dernière version fonctionnelle.
1. Dupliquez le fichier [`parameters_sample.py`](parameters_sample.py) vers `parameters.py`, et configurez-le avec vos clés d'accès aux API. Il vous faut :
   - Un ou plusieurs comptes Twitter qui serviront à indexer les Tweets.
   - Un compte Twitter développeur. Pour se faire, demandez un accès développeur sur le portail suivant : https://developer.twitter.com
   - Et optionnellement un serveur MySQL (Sinon, le serveur utilise SQLite).
2. Installez les librairies Python nécessaires : `pip install -r requirements.txt`

Si êtes sous Windows ou MacOS, il est recommandé d'installer en plus la librairie PyReadline : `pip install pyreadline`

Pour activer l'interface web via Apache et/ou le démarrage automatique du serveur, consultez [`../configs/README.md`](../configs/README.md).

Si vous utilisez MySQL, vous pouvez sauvegarder automatiquement (Tâche Cron) ou manuellement la base de données du serveur AOTF en exécutant le script [`mysqldump_backup.py`](../maintenance/mysqldump_backup.py). Ce script crée des dumps MySQL qui sont placés dans le répertoire [`../backups`](../backups). Le serveur AOTF n'a pas besoin d'être éteint. Pour plus d'informations, consultez le fichier [`Stratégie_de_sauvegarde.md`](../doc/Stratégie_de_sauvegarde.md).


## Utilisation

1. Si vous êtes connecté en SSH sur un serveur, créez d'abord une fenêtre : `screen -S twitter`
2. Lancez le serveur : `python3 app.py`

Ceci lance le serveur et vous met en ligne de commande. Si vous souhaitez quitter la fenêtre en laissant le serveur tourner, faites `Ctrl + A + D`.

Pour arrêter le serveur, vous pouvez soit exécuter la commande `stop` dans sa ligne de commande, soit lui envoyer un signal `SIGTERM`.
S’il utilise une base de données MySQL, vous pouvez aussi le tuer avec `Ctrl + C` ou un signal `SIGKILL`. Ceci n'est pas embêtant pour la cohérence des données.

Pendant l'exécution du serveur (Hors des phases de démarrage et d'arrêt), les commandes suivantes sont disponibles :
* `query [URL de l'illustration]` : Lancer une requête et voir son état. Il faut donc relancer cette commande pour obtenir l'état et les résultats de la requête. Cette commande fonctionne de manière similaire à l'endpoint `/query` de l'API HTTP.
* `scan [Nom du compte à scanner]` : Indexer ou mettre à jour l'indexation des Tweets d'un compte Twitter.
* `search [URL du fichier image] [Optionnel : Nom du compte Twitter sur lequel rechercher]` : Rechercher une image dans toute la base de données, ou sur un compte en particulier. Permet une utilisation plus souple du serveur. Comme pour la commande `query`, il faut relancer la commande pour obtenir l'état et les résultats de la recherche.
* `stats` : Afficher des statistiques de la base de données.
* `threads` : Afficher les threads et ce qu'ils font.
* `queues` : Afficher la taille des files d'attente.
* `metrics`: Afficher les mesures de temps d'exécution. Le paramètre `ENABLE_METRICS` doit être sur `True` pour autoriser le serveur à mesurer des temps d'exécution. Ces mesures ont étés placées à des endroits précis du traitement des requêtes.
* `stacks` : Ecrire les piles d'appels des threads dans un fichier `stacktrace.log`. Si un thread est bloqué, cette commande est très utile pour comprendre où il coincé, et ainsi débugger.
* `stop` : Arrêter le serveur.
* `help` : Afficher l'aider.


## Fonctionnalités

* Base de données stockant les comptes et les Tweets.
* Moteur de calcul de l'empreinte d'une image (Moteur CBIR, reposant sur l'algorithme pHash).
* Parallélisme : 2 pipelines de traitement, divisés en étapes séparés dans des threads de traitement, avec files d'attentes :
  - Traitement des requêtes des utilisateurs, en 3 étapes, exécutées l'une après l'autres. Voir [`threads/user_pipeline`](threads/user_pipeline).
  - Traitement des requêtes d'indexation / de scan d'un comte Twitter, en 4 étapes parallèles. Voir [`threads/scan_pipeline`](threads/scan_pipeline).
* Traitement des requêtes des utilisateurs en 3 étapes :
  - **Etape 1 :** Link Finder : Recherche des comptes Twitter de l'artiste, et recherche du fichier de l'illustration. Classe principale : [`Link_Finder`](link_finder/class_Link_Finder.py), dans le module [`link_finder`](link_finder).
  - **Etape 2 :** Tweets Indexer : Lancement de l'indexation / du scan des comptes Twitter trouvés dans l'autre pipeline, et surveillance de l'avancement de ce traitement.
  - **Etape 3 :** Recherche inversée d'image. Classe principale : [`Reverse_Searcher`](tweet_finder/class_Reverse_Searcher.py), dans le module [`tweet_finder`](tweet_finder).
* Traitement des requêtes de scan en 3 étapes parallèles (Module [`tweet_finder`](tweet_finder)) :
  - **Etape A :** API de recherche : Listage des Tweets des comptes Twitter trouvés. Classe principale : [`Tweets_Lister_with_SearchAPI`](tweet_finder/class_Tweets_Lister_with_SearchAPI.py).
  - **Etape B :** API de timeline : Listage des Tweets des comptes Twitter trouvés. Classe principale : [`Tweets_Lister_with_TimelineAPI`](tweet_finder/class_Tweets_Lister_with_TimelineAPI.py).
    Lire pourquoi il y a deux systèmes de listage, soit deux API utilisées, dans le fichier [`Limites_de_scan_des_comptes_Twitter.md`](../doc/Limites_de_scan_des_comptes_Twitter.md). Pour faire simple : L'API de timeline est limitée aux 3 200 Tweets les plus récents des comptes à indexer (Retweets inclus), et l'API de recherche est limité à ce que Twitter indexent dans leur recherche. Utiliser les deux API permet d'être le plus exhaustif possible lors de l'indexation des comptes qui ont plus de 3 200 Tweets.
  - **Etape C :** Indexeur : Analyse et indexation de tous les Tweets trouvés par les étapes de listage (Tous les comptes sont mélangés). Classe principale : [`Tweets_Indexer`](tweet_finder/class_Tweets_Indexer.py).
* Serveur web pour l'API HTTP qui renvoit les statuts des requêtes, avec les éventuels résultats, ou une erreur s'il y a un problème. Lire le fichier [`API_HTTP.md`](../doc/API_HTTP.md).
* Limite du nombre de requête en cours de traitement par adresse IP.
* Possibilité de lancer en mode multi-processus (Paramètre `ENABLE_MULTIPROCESSING`), plus lourd mais plus efficace pour traiter des requêtes (Des utilisateurs et de scans) en parallèle. Les threads sont alors contenus dans des processus. Voir l'arbre des processus et des threads plus bas.
* Mémoire partagée entre tous les threads dans l'objet [`Shared_Memory`](shared_memory/class_Shared_Memory.py) du module [`shared_memory`](shared_memory) (Avec la librairie Pyro5 si démarré en mode multi-processus).
* Threads de maintenance :
  - Délestage automatique des anciennes requêtes terminées.
  - Lancement de mises à jour automatiques des comptes Twitter dans la base de données. Essaye au maximum de répartir les mises à jour dans le temps.
  - Retentative d'indexation de Tweets dont au moins une image a échouée (Et que cette erreur n'est pas identifiée comme insolvable dans le code, voir [`get_tweet_image()`](tweet_finder/utils/get_tweet_image.py)). Ce thread passe ses Tweets à l'étape C.
  - Suppression des curseurs d'indexation avec l'API de recherche, car l'indexation sur le moteur de recherche de Twitter est très fluctuante. Comme le thread de mise à jour, essaye au maximum de répartir les lancements d'indexations dans le temps.
* Collecteur d'erreurs : Tous les threads sont exécutés dans une instance du collecteur d'erreurs. Stocke l'erreur dans un fichier, met l'éventuelle requête en cours de traitement en situation d'erreur / échec, et redémarre le thread.
* Support des signaux `SIGTERM`, `SIGINT` et `SIGHUP`, avec arrêt propre lorsque l'un d'entre eux est reçu.


## Architecture du code

Script [`app.py`](app.py) : Script central, crée et gère les threads de traitement, la ligne de commande, les files d'attentes des requêtes, et le serveur HTTP.

* Module [`app`](app) : Dépendances directes du script [`app.py`](app.py). Contient des éléments qu'il utilise directement, dont par exemple le gestionnaire des threads (Classe `Threads_Manager`) ou l'entrée en ligne de commande (Classe `Command_Line_Interface`).

* Module [`threads`](threads) : Procédures des threads du serveur AOTF, ainsi que les fonctions pour les démarrer. Voir le [`README.md`](threads/README.md) de ce module pour plus de détails.
  - Module [`user_pipeline`](threads/user_pipeline) : Pipeline de traitement des requêtes utilisateurs, en 3 étapes : Link Finder, lancement si nécessaire et suivi du scan du ou des comptes Twitter dans l'autre pipeline, et recherche inversée de l'image de requête.
  - Module [`scan_pipeline`](threads/scan_pipeline) : Pipeline de traitement des requêtes de scan d'un compte Twitter, en 3 étapes paralléles.
  - Module [`http_server`](threads/http_server) : Serveur HTTP intégré, qui contient uniquement l'API.
  - Module [`maintenance`](threads/maintenance) : Threads de maintenance, dont celui de mise à jour automatique.

* Module [`shared_memory`](shared_memory) : Mémoire partagée dans un serveur, permet le multi-processus et de faire potentiellement un système distribué.
  Peut être utilisée comme un serveur Pyro (Indispensable au multi-processus), ou sinon comme un simple objet Python.

* Module [`tweet_finder`](tweet_finder), contenant plusieurs classes : Moteur de recherche d'image par le contenu pour des comptes Twitter et des Tweets. Gère le stockage et la recherche d'image inversée.
  - Module [`utils`](tweet_finder/utils) : Contient un outil pour la classe ci-dessus.
  - Module [`cbir_engine`](tweet_finder/cbir_engine) : Contient les classes du moteur de recherche d'image par le contenu. Voir le [`README.md`](tweet_finder/cbir_engine/README.md) de ce module pour plus de détails.
  - Module [`database`](tweet_finder/database) : Contient les classes de gestion et d'accès à la base de données.
  - Module [`twitter`](tweet_finder/twitter) : Contient les classe d'abstraction aux librairies qui permettent d'utiliser les API Twitter.

* Module [`link_finder`](link_finder), classe [`Link_Finder`](link_finder/class_Link_Finder.py) : Classe centrale de la partie Link Finder. Permet de trouver les URL des images et les noms des comptes Twitter des artistes.
  - Module [`supported_websites`](link_finder/supported_websites) : Contient une classe pour chaque site supporté. Voir le [`README.md`](link_finder/supported_websites/README.md) de ce module pour plus de détails.
    - Module [`utils`](link_finder/supported_websites/utils) : Contient des outils pour les classes ci-dessus.


## Architecture à l'exécution

![Architecture du serveur](../doc/Architecture_du_serveur.png)


## Arbre des processus et threads à l'exécution

En mode multi-processus, le serveur AOTF exécute des processus et des threads. Les étapes de traitement nécessitant de la puissance de calcul sont exécutées seules dans des processus conteneurs. Les autres sont exécutées dans des processus regroupant des threads. Ainsi, les processus et threads suivants sont exécutés :

* Processus `app.py` :
  - Thread `thread_pyro_server` (La librairie Pyro5 exécute d'autres threads) : Mémoire partagée.
  - Processus conteneur :
    - Plusieurs threads `thread_step_1_link_finder` : Etape 1, Link Finder.
    - Plusieurs threads `thread_step_2_tweets_indexer` : Etape 2, vérification de l'indexation et de la mise à jour.
  - Plusieurs processus conteneurs (Possédant chacun un ou deux threads) :
    - Thread(s) `thread_step_3_reverse_search` : Etape 3, Recherche par image.
  - Processus conteneur :
    - Plusieurs threads `thread_step_A_SearchAPI_list_account_tweets` : Etape A, listage avec l'API de recherche.
    - Plusieurs threads `thread_step_B_TimelineAPI_list_account_tweets` : Etape B, listage avec l'API de timeline.
  - Plusieurs processus conteneurs (Possédant chacun un ou deux threads) :
    - Thread(s) `thread_step_C_index_tweets` : Etape C, indexation des Tweets trouvés.
  - Processus conteneur :
    - Thread `thread_http_server` : Serveur HTTP, API du serveur.
  - Processus conteneur :
    - Thread `thread_auto_update_accounts` : Mise à jour automatique.
    - Thread `thread_reset_SearchAPI_cursors` : Délestage des requêtes.
    - Thread `thread_remove_finished_requests` : Réinitialisation des curseurs de l'API de recherche.
    - Thread `thread_retry_failed_tweets` : Retentative d'indexation de Tweets échoués.

Le nombre de threads de traitement sont définis dans [`constants.py`](utils/constants.py), et dépendent du nombre de comptes Twitter d'indexation (Liste `TWITTER_API_KEYS` dans votre fichier `parameters.py`).

Si le mode multi-processus est désactivé, les processus conteneurs disparaissent, et les threads sont éxécutés directement par `app.py`.


## Philosophie

* **Cohérence des données de la BDD à tout moment :** L'ajout ou la modifications de données dans la base de données est pensée pour qu'un arrêt brutal (Plantage ou kill) d'un thread de traitement ou du serveur complet n'ait pas d'impact sur la cohérence des données. Ceci est notamment le cas pour les curseurs d'indexation, qui sont enregistrés une fois que tous les Tweets ont bien étés enregistrés sans qu'un thread ait planté. Cela permet aussi faire un Dump MySQL à n'importe quel moment, sans avoir à arrêter le serveur.

* **Cross-platform :** Le code est pensé pour être cross-platform. Il peut être exécuté facilement sur n'importe que système muni de l'interpréteur CPython, et ne nécessite aucune dépendance externe, mis à part optionnellement un serveur MySQL.

* **Légèreté relative du serveur :** Même si Python n'est pas un langage connu pour son efficacité par rapport aux ressources qu'il consomme, AOTF est tout de même un moteur de recherche par image léger, puisqu'il ne fait ses recherches que sur une fraction de la base de données, et donc ne nécessite beaucoup moins de ressoures que s'il faisait des recherches dans toute sa BDD. Voir [`Réflexions_et_conclusions.md`](../doc/Réflexions_et_conclusions.md) pour plus de détails.


## Notes

* Les requêtes sur le serveur sont identifiées par l'URL de l'illustration de requête.

* Lorsque l'on parle de l'URL d'une requête, ou de l'URL d'une illustration, on parle de l'**URL de la page web** qui contient l'illustration, et non l'URL menant directement à l'image.
  Exemple :
  - Ceci est une URL d'illustration, elle peut être traitée par le serveur : https://derpibooru.org/images/639483
  - Ceci est une URL menant directement à l'image, elle sera rejetée par serveur : https://derpicdn.net/img/view/2014/5/28/639483.jpg

* Si l'image d'un Tweet a été perdue par Twitter, ou qu'il s'est produit une erreur, elle est de toutes manières enregistrée dans la base de données, et son empreinte est mise à `NULL` (Mais son nom est quand même enregistré).
  S’il se produit une erreur, elle sera journalisée ici.

* Le serveur AOTF ne supprime aucun enregistrement de sa base de données ! C'est le script de maintenance [`remove_deleted_accounts.py`](../maintenance/remove_deleted_accounts.py) qui permet d'effacer des comptes Twitter, et le script [`cleanup_database.py`](../maintenance/cleanup_database.py) qui permet d'effacer les Tweets sans compte associé.
