# Module Tweet Finder

Le Tweet Finder est l'une des deux grandes parties du serveur "Artist on Twitter Finder", avec le Link Finder.

La classe `CBIR_Engine_with_Database` permet de faire :
* L'indexation des Tweets d'un compte Twitter (Seulement ceux qui n'ont pas déjà été indexés) :
  - Va chercher les Tweets d'un compte Twitter à partie du dernier scan (Ou tous les Tweet si le compte n'a pas été encore scanné) :
    - Via la librairie GetOldTweets3, module `lib_GetOldTweets3`,
    - Ou via la librairie Tweepy pour l'API Twitter publique, module `twitter`,
  - Calcul la liste des caractéristiques de toutes les images pour chaque Tweet, module `cbir_engine`,
  - Et stocke pour chaque Tweet ces listes dans la base de données, module `database`;

* Et la recherche d'un Tweet à partir d'une image, et éventuellement du compte Twitter sur lequel chercher :
  - Calcul la liste des caractéristiques de l'image de recherche, module `cbir_engine`,
  - Obtient l'itérateur sur la base de données, module `database`,
  - Calcul la distance entre l'image de requête et chaque image de l'itérateur, module `cbir_engine`,
  - Retourne le ou les Tweets correspondant.


## Sous-modules

* `cbir_engine` : Moteur de recherche d'image par le contenu ("Content-Based Image Retrieval", CBIR), mais ne gère pas de base de données. Ce moteur est généraliste, il peut donc être réutilisé dans un autre projet, à condition de réécrire un accès à une base de données et l'itération sur cette base (Pour la recherche).
* `database` : Couche d'abstraction à l'utilisation de la base de données. Cette couche est spécialisée pour notre projet.
* `twitter` : Couche d'abstraction à l'utilisation de l'API Twitter via la librairie Python Tweepy. Est spécialisé, contient uniquement les fonctions dont nous avons besoin.
* `utils` : Divers fonctions utiles.

La classe `CBIR_Engine_with_Database` fait le lien entre le moteur CBIR et la base de données, mais est spécialisé pour les images dans des Tweets.
