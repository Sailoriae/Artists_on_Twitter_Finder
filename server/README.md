# Artists on Twitter Finder : Serveur

Le serveur de "Artists on Twitter Finder" exécute tout le traitement des requêtes, et gère sa base de données.
Il possède une API HTTP pour recevoir les requêtes, et y répondre.
Lorsqu'il est démarré, il affiche une interface en ligne de commande. Tapez `help` dans cette interface pour avoir la liste des commandes disponibles.


## Installation

1. Dupliquez le fichier [`parameters_sample.py`](parameters_sample.py) vers `parameters.py`, et configurez-le avec vos clés d'accès aux API. Il vous faut :
   - Un ou plusieurs comptes Twitter qui serviront à indexer les Tweets.
   - Un compte Twitter développeur. Pour se faire, demandez un accès développeur sur le portail suivant : https://developer.twitter.com
   - Et optionnellement un serveur MySQL (Sinon, le serveur utilise SQLite).
2. Installez les librairies Python nécessaires : `pip install -r requirements.txt`


## Utilisation

1. Si vous êtes connecté en SSH sur un serveur, créez d'abord une fenêtre : `screen -S twitter`
2. Lancez le serveur : `python3 app.py`

Ceci lance le serveur et vous met en ligne de commande. Si vous souhaitez quitter la fenêtre en laissant le serveur tourner, faites `Crtl + A + D`.

Pour arrêter le serveur, vous pouvez soit éxécuter la commande `stop` dans sa ligne de commande, soit lui envoyer un signal `SIGTERM`.
Si il utilise une base de données MySQL, vous pouvez aussi le tuer avec `Ctrl + C` ou un signal `SIGKILL`. Ceci n'est pas embêtant pour la cohérence des données.


## Fonctionnalités

* Base de données stockant les comptes et les Tweets.
* Moteur de calcul de l'empreinte d'une image (Moteur CBIR, reposant sur l'algorithme pHash).
* Parallélisme : 2 pipelines de traitement, divisés en étapes séparés dans des threads de traitement, avec files d'attentes :
  - Traitement des requêtes des utilisateurs, en 3 étapes, exécutées l'une après l'autres. Voir [`app/user_pipeline`](app/user_pipeline).
  - Traitement des requêtes d'indexation / de scan d'un comte Twitter, en 4 étapes paralléles. Voir [`app/scan_pipeline`](app/scan_pipeline).
* Traitement des requêtes des utilisateurs en 3 étapes :
  - **Etape 1 :** Link Finder : Recherche des comptes Twitter de l'artiste, et recherche du fichier de l'illustration. Classe principale : [`Link_Finder`](link_finder/class_Link_Finder.py), dans le module [`link_finder`](link_finder).
  - **Etape 2 :** Tweets Indexer : Lancement de l'indexation / du scan des comptes Twitter trouvés dans l'autre pipeline, et surveillance de l'avancement de ce traitement.
  - **Etape 3 :** Recherche inversée d'image. Classe principale : [`Reverse_Searcher`](tweet_finder/class_Reverse_Searcher.py), dans le module [`tweet_finder`](tweet_finder).
* Traitement des requêtes de scan en 3 étapes paralléles (Module [`tweet_finder`](tweet_finder)) :
  - **Etape A :** API de recherche : Listage des Tweets des comptes Twitter trouvés. Classe principale : [`Tweets_Lister_with_SearchAPI`](tweet_finder/class_Tweets_Lister_with_SearchAPI.py).
  - **Etape B :** API de timeline : Listage des Tweets des comptes Twitter trouvés. Classe principale : [`Tweets_Lister_with_TimelineAPI`](tweet_finder/class_Tweets_Lister_with_TimelineAPI.py).
    Voir pourquoi il y a deux systèmes de listage, soit deux API utilisées, dans [`../doc/Limites_de_scan_des_comptes_Twitter.md`](../doc/Limites_de_scan_des_comptes_Twitter.md). Pour faire simple : L'API de timeline est limitée aux 3 200 Tweets les plus récents des comptes à indexer (Retweets inclus), et l'API de recherche est limité à ce que Twitter indexent dans leur recherche. Utiliser les deux API permet d'être le plus exhaustif possible lors de l'indexation des comptes qui ont plus de 3 200 Tweets.
  - **Etape C :** Indexeur : Analyse et indexation de tous les Tweets trouvés par les étapes de listage (Tous les comptes sont mélangés). Classe principale : [`Tweets_Indexer`](tweet_finder/class_Tweets_Indexer.py).
* Serveur web pour l'API HTTP qui renvoit les status des requêtes, avec les éventuels résultats, ou une erreur s'il y a un problème. Voir [`../doc/API_HTTP.md`](../doc/API_HTTP.md).
* Possibilité de lancer en mode multi-processus (`ENABLE_MULTIPROCESSING`), plus lourd mais plus efficace pour traiter des requêtes (Des utilisateurs et de scans) en paralléle. Note : Dans toute la documentation, on parle toujours de threads, mais **un thread peut devenir un processus en mode multi-processus**.
* Mémoire partagée entre tous les threads dans l'objet [`Shared_Memory`](shared_memory/class_Shared_Memory.py) du module [`shared_memory`](shared_memory) (Avec la librairie Pyro4 si démarré en mode multi-processus).
* Limite du nombre de requête en cours de traitement par adresse IP.
* Threads de maintenance :
  - Délestage automatique des anciennes requêtes terminées.
  - Lancement de mises à jour automatiques des comptes Twitter dans la base de données. Essaye au maximum de répartir les mises à jour dans le temps.
  - Retentative d'indexation de Tweets dont au moins une image a échouée (Et que cette erreur n'est pas identifiée comme insolvable dans le code, voir [`get_tweet_image()`](tweet_finder/utils/get_tweet_image.py)). Ce thread passe ses Tweets à l'étape C.
  - Suppression des curseurs d'indexation avec l'API de recherche, car l'indexation sur le moteur de recherche de Twitter est très fluctuante. Comme le thread de mise à jour, essaye au maximum de répartir les lancement d'indexations dans le temps.
* Collecteur d'erreurs : Tous les threads sont éxécuté dans une instance du collecteur d'erreurs. Stocke l'erreur dans un fichier, met l'éventuelle requête en cours de traitement en situation d'erreur / échec, et redémarre le thread.


## Architecture du code

Script [`app.py`](app.py) : Script central, crée et gère les threads de traitement, la ligne de commande, les files d'attentes des requêtes, et le serveur HTTP.

* Module [`app`](app) : Dépendances du script [`app.py`](app.py). Contient les procédures de ses threads, et ses classes. Voir le [`README.md`](app/README.md) de ce module pour plus de détails.
  - Module [`user_pipeline`](app/user_pipeline) : Pipeline de traitement des requêtes utilisateurs, en 3 étapes : Link Finder, lancement si nécessaire et suivi du scan du ou des comptes Twitter dans l'autre pipeline, et recherche inversée de l'image de requête.
  - Module [`scan_pipeline`](app/scan_pipeline) : Pipeline de traitement des requêtes de scan d'un compte Twitter, en 3 étapes paralléles.

* Module [`shared_memory`](shared_memory) : Mémoire partagée dans un serveur, permet le multi-processing et de faire potentiellement un système distribué.
  Peut être utilisée comme un serveur PYRO (Indispensable au multi-processus), ou sinon comme un simple objet Python.

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


## Arbre des processus et threads à l'éxécution

En mode multi-processus, le serveur AOTF éxécute des processus et des threads. Les étapes de traitement nécessitant de la puissance de calcul sont éxécutés en tant que procesus. Les autres son éxécutés dans des processus regroupant des threads. Ainsi, les processus et threads suivants sont éxécutés :

* Processus `app.py` :
  - Thread `thread_pyro_server` (La librairie Pyro4 éxécute d'autres threads) : Mémoire partagée.
  - Processus de groupe de threads :
    - Plusieurs threads `thread_step_1_link_finder` (Nombre défini dans `parameters.py`) : Etape 1, Link Finder.
  - Processus de group de threads :
    - Plusieurs threads `thread_step_2_tweets_indexer` (Nombre défini dans `parameters.py`) : Etape 2, vérification de l'indexation et de la mise à jour.
  - Plusieurs processus `thread_step_3_reverse_search` (Nombre défini dans `parameters.py`) : Etape 3, Recherche par image.
  - Processus de group de threads :
    - Plusieurs threads `thread_step_A_SearchAPI_list_account_tweets` (Nombre défini dans `parameters.py`) : Etape A, listage avec l'API de recherche.
  - Processus de group de threads :
    - Plusieurs threads `thread_step_B_TimelineAPI_list_account_tweets` (Nombre défini dans `parameters.py`) : Etape B, listage avec l'API de timeline.
  - Plusieurs processus `thread_step_C_index_account_tweets` (Nombre défini dans `parameters.py`) : Etape C, indexation des Tweets trouvés.
  - Processus `thread_http_server` : Serveur HTTP, API du serveur.
  - Processus de groupe de threads :
    - Thread `thread_auto_update_accounts` : Mise à jour automatique.
    - Thread `thread_reset_SearchAPI_cursors` : Délestage des requêtes.
    - Thread `thread_remove_finished_requests` : Réinitialisation des curseurs de l'API de recherche.
    - Thread `thread_retry_failed_tweets` : Retentative d'indexation de Tweets échoués.

Si le mode multi-processus est désactivé, tous les processus deviennent des threads (Sauf `app.py`), et les processus de groupes de threads disparaissent.


## Notes

* Les requêtes sur le serveur sont identifiées par l'URL de l'illustration de requête.

* Lorsque l'on parle de l'URL d'une requête, ou de l'URL d'une illustration, on parle de l'**URL de la page web** qui contient l'illustration, et non l'URL menant directement à l'image.
  Exemple :
  - Ceci est une URL d'illustration, elle peut être traitée par le serveur : https://danbooru.donmai.us/posts/3991989
  - Ceci est une URL menant directement à l'image, elle sera rejetée par serveur : https://danbooru.donmai.us/data/__hatsune_miku_vocaloid_drawn_by_bibboss39__cac99a60fa84a778d5b048daec05e7b1.jpg

* La date de dernière mise à jour d'un compte Twitter est mise dans la base de données à la fin des indexations (Grâce à une intruction d'enregistrement passée dans la file d'attente de l'indexeur). Si l'un des threads de traitement plante, la requête est mise en erreur, et aucune date n'est enregistrée. Ainsi, l'intégralité des Tweets qu'il est possible de récupérer ont étés analysés et ceux avec une ou plusieurs image sont dans la base de données.

* Si l'image d'un Tweet a été perdue par Twitter, ou qu'il s'est produit une erreur, elle est de toutes manières enregistrée dans la base de données, et son empreinte est mise à `NULL` (Mais son nom est quand même enregistré).
  Si il s'est produit une erreur, elle sont journalisées ici.

* Les curseurs d'indexation sont enregistrés une fois l'indexation terminée. D'une manière générale, l'ajout ou la modifications de données dans la base de données est pensée pour qu'un arrêt brutal (Crash ou kill) d'un thread ou du serveur complet n'ait pas d'impact sur la cohérence des données.
