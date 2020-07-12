# Artist on Twitter Finder

Voici un moteur de recherche inversé d'image, spécialisé dans les illustrations postées par des artistes sur Twitter.

Contrairement aux moteurs de recherche inversé d'image généralistes, comme Google Images ou TinEye, celui-ci est très spécialisé : A partir d'une illustration postée sur un des sites supportés (DeviantArt et Pixiv pour le moment), il va chercher si l'artiste de cette illustration posède un compte Twitter, et si oui, va chercher son ou ses Tweets contenant cette illustration.


## Installation

1. Configurer le fichier `parametres.py` avec vos clés d'accès aux API.
2. Installer les bibliothèques : `pip install -r requirements.txt`


## Utilisation

1. Si vous êtes connecté en SSH sur un serveur, créez d'abord une fenêtre : `screen -S temp`
2. Lancez le serveur avec IPython : `ipython app.py`

Ceci lance le serveur et vous met en ligne de commande. Si vous souhaitez quitter la fenêtre en laissant le serveur tourner, faites `Crtl + A + D`.


## Architecture du code

Script `app.py` : Script central, crée et gère les threads de traitement, la ligne de commande, les files d'attentes des requêtes, et le serveur HTTP.

* Classe `CBIR_Engine_with_Database` : Moteur de recherche d'image par le contenu pour des comptes Twitter et des Tweets. Gère le stockage et la recherche d'image inversée.
  - Module `utils`: Contient un outil pour la classe ci-dessus.
  - Module `cbir_engine` : Contient les classes du moteur de recherche d'image par le contenu. Voir le `README.md` de ce module pour plus de détails.
  - Module `database` : Contient les classes de gestion et d'accès à la base de données.
  - Module `twitter` : Contient la classe d'accès à l'API Twitter.
  - Librairie `GetOldTweets3` : Permet d'obtenir les tweets d'un compte. Incluse car elle a été modifiée.

* Classe `Link_Finder` : Classe centrale de la partie Link Finder. Permet de trouver les URL des images et les noms des comptes Twitter des artistes.
  - Module `link_finder` : Contient une classe pour chaque site supporté. Voir le `README.md` de ce module pour plus de détails.
    - Module `link_finder\utils` : Contient des outils pour les classes ci-dessus.
