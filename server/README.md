# Artist on Twitter Finder : Serveur

Ceci est la plus grosse partie de ce projet : Le serveur. C'est lui qui fait tout le traitement et gère sa base de données.

## Installation

1. Configurer le fichier `parametres.py` avec vos clés d'accès aux API.
2. Installer les bibliothèques : `pip install -r requirements.txt`


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
  - Module `link_finder` : Contient une classe pour chaque site supporté. Voir le `README.md` de ce module pour plus de détails.
    - Module `link_finder\utils` : Contient des outils pour les classes ci-dessus.
