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


## Modules

Ce projet comporte plusieurs modules qui peuvent être utilisés indépendamments :
* `cbir_engine` : Moteur de recherche d'image par le contenu ("Content-Based Image Retrieval", CBIR), mais ne gère pas de base de données. Ce moteur est généraliste, il peut donc être réutilisé dans un autre projet, à condition de réécrire un accès à une base de données et l'itération sur cette base (Pour la recherche).
* `database` : Couche d'abstraction à l'utilisation de la base de données. Cette couche est spécialisée pour notre projet.
* `link_finder` : Moteur de recherche de comptes Twitter d'un artiste à partir d'une illustration postée sur un des sites supportés.
* `twitter` : Couche d'abstraction à l'utilisation de l'API Twitter via la librairie Python Tweepy. Est spécialisé, contient uniquement les fonctions dont nous avons besoin.
* `utils` : Divers fonctions utiles.

La classe `CBIR_Engine_with_Database` fait le lien entre le moteur CBIR et la base de données, mais est spécialisé pour les images dans des Tweets.
La classe `Link_Finder` permet d'utiliser le Link Finder sans avoir à sélectionner le site.


## Utilisation de l'API

Le serveur est utilisable via un serveur HTTP, depuis le même serveur, ou l'extérieur, en faisant un proxy sur Apache ou Nginx. Ne pas ouvrir le port du serveur !

Les requêtes sont indentifiées par leur URL. La méthode pour lancer une procédure ou obtenir le résultat est la même : `GET /url=[URL de l'illustration de requête]`

Par exemple : `GET /?url=https://www.deviantart.com/serafleur/art/Sailor-Moon-604185347`

Le serveur répond par un JSON qui contient toujours les mêmes champs :
```
{
	"status" : "END",
	"results" : [
		{ "tweet_id" : 797039787534262272, "distance" : 0.4124855017771303 },
	],
	"error" : ""
}
```

Liste des status possibles :
- `WAIT_LINK_FINDER` : En attente de traitement par un thread de Link Finder.
- `LINK_FINDER` : En cours de traitement par un thread de Link Finder.
- `WAIT_INDEX_ACCOUNT_TWEETS` : En attente de traitement par un thread d'indexation des tweet d'un compte Twitter.
- `INDEX_ACCOUNT_TWEETS` : En cours de traitement par un thread d'indexation des tweets d'un compte Twitter.
- `WAIT_IMAGE_REVERSE_SEARCH` : En attente de traitement par un thread de recherche d'image inversée.
- `IMAGE_REVERSE_SEARCH` : En cours de traitement par un thread de recherche d'image inversée.
- `END` : Fin de traitement.

Liste des erreurs possibles :
- `NO_URL_FIELD` : Il n'y a pas de paramètre / argument `url` dans l'URL de requête.
- `INVALID_URL` : L'URL passée en paramètre est invalide.
- `UNSUPPORTED_WEBSITE` : Le site passé en paramètre n'est pas supporté.
- `NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST` : Aucun compte Twitter trouvé pour l'artiste de l'illustration.

La liste `results` peut être vide, ou comporter plusieurs résultats. Ils sont alors classés par ordre croissant de distance avec l'illustration de requête.
