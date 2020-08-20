# Artists on Twitter Finder : Serveur

Le serveur de "Artists on Twitter Finder" exécute tout le traitement des requêtes, et gère sa base de données.
Il possède une API HTTP pour recevoir les requêtes, et y répondre.
Lorsqu'il est démarré, il affiche une interface en ligne de commande. Tapez `help` dans cette interface pour avoir la liste des commandes disponibles.


## Installation

1. Configurer le fichier `parametres.py` avec vos clés d'accès aux API.
2. Sous Linux, installer D'ABORD les dépendances de la librairie OpenCV-Python : `sudo apt install libsm6 libxext6 libxrender-dev`
3. Installer les librairies nécessaires : `pip install -r requirements.txt`


## Utilisation

1. Si vous êtes connecté en SSH sur un serveur, créez d'abord une fenêtre : `screen -S twitter`
2. Lancez le serveur : `python3 app.py`

Ceci lance le serveur et vous met en ligne de commande. Si vous souhaitez quitter la fenêtre en laissant le serveur tourner, faites `Crtl + A + D`.


## Fonctionnalités

* Base de données stockant les comptes et les Tweets.
* Moteur de calcul de caractéristiques d'une image (Moteur CBIR).
* Parallélisme : 2 pipelines de traitement, divisés en étapes séparés dans des threads de traitement, avec files d'attentes :
  - Traitement des requêtes des utilisateurs, en 4 étapes, exécutées l'une après l'autres. Voir `app/user_pipeline`.
  - Traitement des requêtes d'indexation / de scan d'un comte Twitter, en 4 étapes paralléles. Voir `app/scan_pipeline`.
* Traitement des requêtes des utilisateurs en 4 étapes :
  - Link Finder : Recherche des comptes Twitter de l'artiste, et recherche du fichier de l'illustration. Classe principale : `Link_Finder`, dans le module `link_finder`.
  - Tweets Indexer : Lancement de l'indexation / du scan des comptes Twitter trouvés dans l'autre pipeline, et surveillance de l'avancement de ce traitement.
  - Recherche inversée d'image. Classe principale : `Reverse_Searcher`, dans le module `tweet_finder`.
  - Filtrage des résultats de la recherche inversée, car il peut y avoir des faux positifs.
* Traitement des requêtes de scan en 4 étapes paralléles (Module `tweet_finder`) :
  - GetOldTweets3 : Listage des Tweets des comptes Twitter trouvés. Classe principale : `Tweets_Lister_with_GetOldTweets3`.
  - GetOldTweets3 : Analyse et indexation des Tweets trouvés. L'analyse consiste au calcul des caractéristiques de l'image avec le moteur CBIR. Classe principale : `Tweets_Indexer_with_GetOldTweets3`.
  - API Twitter publique via Tweepy : Listage des Tweets des comptes Twitter trouvés. Classe principale : `Tweets_Lister_with_TwitterAPI`.
  - API Twitter publique via Tweepy : Analyse et indexation des Tweets des comptes Twitter trouvés. Classe principale : `Tweets_Indexer_with_TwitterAPI`.
  - Voir pourquoi il y a deux systèmes d'indexation dans `../doc/Limites_de_scan_des_comptes_Twitter.md`.
* Serveur web pour l'API HTTP qui renvoit les status des requêtes, avec les éventuels résultats, ou une erreur s'il y a un problème. Voir `doc/API_HTTP.md`.
* Mémoire partagée entre tous les threads dans l'objet `Shared_Memory` du module `shared_memory` (Avec la librairie Pyro4).
* Limite du nombre de requête en cours de traitement par adresse IP.
* Thread de délestage automatique des anciennes requêtes terminées.
* Thread de lancement de mises à jour automatiques des comptes Twitter dans la base de données.
* Collecteur d'erreurs : Tous les threads sont éxécuté dans une instance du collecteur d'erreurs. Stocke l'erreur dans un fichier, met l'éventuelle requête en cours de traitement en situation d'erreur / échec, et redémarre le thread.


## Architecture du code

Script `app.py` : Script central, crée et gère les threads de traitement, la ligne de commande, les files d'attentes des requêtes, et le serveur HTTP.

* Module `app` : Dépendances du script `app.py`. Contient les procédures de ses threads, et ses classes. Voir le `README.md` de ce module pour plus de détails.
  - Module `user_pipeline` : Pipeline de traitement des requêtes utilisateurs, en 4 étapes : Link Finder, lancement si nécessaire et suivi du scan du ou des comptes Twitter dans l'autre pipeline, recherche inversée de l'image de requête, et filtrage des résultats de cette recherche.
  - Module `scan_pipeline` : Pipeline de traitement des requêtes de scan d'un compte Twitter, en 4 étapes paralléles.

* Module `shared_memory` : Mémoire partagée dans un serveur, permet le multi-processing et de faire potentiellement un système distribué.

* Module `tweet_finder`, contenant plusieurs classes : Moteur de recherche d'image par le contenu pour des comptes Twitter et des Tweets. Gère le stockage et la recherche d'image inversée.
  - Module `utils`: Contient un outil pour la classe ci-dessus.
  - Module `cbir_engine` : Contient les classes du moteur de recherche d'image par le contenu. Voir le `README.md` de ce module pour plus de détails.
  - Module `database` : Contient les classes de gestion et d'accès à la base de données.
  - Module `twitter` : Contient la classe d'accès à l'API Twitter.
  - Librairie `GetOldTweets3` : Permet d'obtenir les tweets d'un compte. Incluse car elle a été modifiée.

* Module `link_finder`, classe `Link_Finder` : Classe centrale de la partie Link Finder. Permet de trouver les URL des images et les noms des comptes Twitter des artistes.
  - Module `supported_websites` : Contient une classe pour chaque site supporté. Voir le `README.md` de ce module pour plus de détails.
    - Module `utils` : Contient des outils pour les classes ci-dessus.


## Architecture à l'exécution

![Architecture du serveur](../doc/Architecture_du_serveur.png)


## Notes

* Les requêtes sur le serveur sont identifiées par l'URL de l'illustration de requête.

* Lorsque l'on parle de l'URL d'une requête, ou de l'URL d'une illustration, on parle de l'**URL de la page web** qui contient l'illustration, et non l'URL menant directement à l'image.
  Exemple :
  - Ceci est une URL d'illustration, elle peut être traitée par le serveur : https://danbooru.donmai.us/posts/3991989
  - Ceci est une URL menant directement à l'image, elle sera rejetée par serveur : https://danbooru.donmai.us/data/__hatsune_miku_vocaloid_drawn_by_bibboss39__cac99a60fa84a778d5b048daec05e7b1.jpg

* La date de dernière mise à jour d'un compte Twitter est mise dans la base de données à la fin des 2 étapes d'indexation (Indexation GOT3 et indexation Twitter API). Si l'un des threads de traitement plante, la requête est mise en erreur, et aucune date n'est enregistrée. Ainsi, l'intégralité des Tweets qu'il est possible de récupérer ont étés analysés et ceux avec une ou plusieurs image sont dans la base de données.
