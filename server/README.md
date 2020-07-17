# Artist on Twitter Finder : Serveur

Le serveur de "Artist on Twitter Finder" exécute tout le traitement des requêtes, et gère sa base de données.
Il possède une API HTTP pour recevoir les requêtes, et y répondre.
Lorsqu'il est démarré, il affiche une interface en ligne de commande. Tapez `help` dans cette interface pour avoir la liste des commandes disponibles.


## Installation

1. Configurer le fichier `parametres.py` avec vos clés d'accès aux API.
2. Installer les librairies nécessaires : `pip install -r requirements.txt`


## Utilisation

1. Si vous êtes connecté en SSH sur un serveur, créez d'abord une fenêtre : `screen -S temp`
2. Lancez le serveur avec IPython : `ipython app.py`

Ceci lance le serveur et vous met en ligne de commande. Si vous souhaitez quitter la fenêtre en laissant le serveur tourner, faites `Crtl + A + D`.


## Architecture du code

Script `app.py` : Script central, crée et gère les threads de traitement, la ligne de commande, les files d'attentes des requêtes, et le serveur HTTP.

* Module `app` : Dépendances du script `app.py`. Contient les procédures de ses threads, et ses classes. Voir le `README.md` de ce module pour plus de détails.

* Module `tweet_finder`, classe `CBIR_Engine_with_Database` : Moteur de recherche d'image par le contenu pour des comptes Twitter et des Tweets. Gère le stockage et la recherche d'image inversée.
  - Module `utils`: Contient un outil pour la classe ci-dessus.
  - Module `cbir_engine` : Contient les classes du moteur de recherche d'image par le contenu. Voir le `README.md` de ce module pour plus de détails.
  - Module `database` : Contient les classes de gestion et d'accès à la base de données.
  - Module `twitter` : Contient la classe d'accès à l'API Twitter.
  - Librairie `GetOldTweets3` : Permet d'obtenir les tweets d'un compte. Incluse car elle a été modifiée.

* Module `link_finder`, classe `Link_Finder` : Classe centrale de la partie Link Finder. Permet de trouver les URL des images et les noms des comptes Twitter des artistes.
  - Module `supported_websites` : Contient une classe pour chaque site supporté. Voir le `README.md` de ce module pour plus de détails.
    - Module `utils` : Contient des outils pour les classes ci-dessus.


## Notes

* Les requêtes sur le serveur sont identifiées par l'URL de l'illustration de requête.

* Lorsque l'on parle de l'URL d'une requête, ou de l'URL d'une illustration, on parle de l'**URL de la page web** qui contient l'illustration, et non l'URL menant directement à l'image.
  Exemple :
  - Ceci est une URL d'illustration, elle peut être traitée par le serveur : https://danbooru.donmai.us/posts/3991989
  - Ceci est une URL menant directement à l'image, elle sera rejetée par serveur : https://danbooru.donmai.us/data/__hatsune_miku_vocaloid_drawn_by_bibboss39__cac99a60fa84a778d5b048daec05e7b1.jpg
