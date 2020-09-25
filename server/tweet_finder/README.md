# Module Tweet Finder

Le Tweet Finder est l'une des deux grandes parties du serveur "Artists on Twitter Finder", avec le Link Finder.

Les classes `Tweets_Indexer_with_SearchAPI` et `Tweets_Indexer_with_TimelineAPI` listent les Tweets de comptes Twitter à partir du dernier scan (Ou tous les Tweet si le compte n'a pas été encore scanné) :
* `Tweets_Indexer_with_SearchAPI` utilise la librairie SNScraper pour l'API Twitter utilisée par l'UI web https://twitter.com/search,
* Et `Tweets_Indexer_with_TimelineAPI` utilise la librairie Tweepy pour l'API Twitter publique, module `twitter`.

Les classes `Tweets_Lister_with_SearchAPI` et `Tweets_Lister_with_TimelineAPI` indexent les Tweets trouvés par leur classe de listage respectives :
1. Calcul de la liste des caractéristiques de toutes les images pour chaque Tweet, module `cbir_engine`, via la classe `CBIR_Engine_for_Tweets_Images`,
2. Stockage ce dans la base de données en les associants à l'ID du Tweet, et l'ID du compte l'ayant Tweeté, module `database`.

L'étape de listage communique ses Tweets trouvés à l'étape d'indexation via un objet queue.Queue(), permettant de paralléliser ces deux étapes.

La classe `Reverse_Searcher` permet de rechercher un Tweet à partir d'une image, et éventuellement du compte Twitter sur lequel chercher :
1. Calcul la liste des caractéristiques de l'image de recherche, module `cbir_engine`,
2. Obtient l'itérateur sur la base de données, module `database`,
3. Calcul la distance entre l'image de requête et chaque image de l'itérateur, module `cbir_engine`,
4. Retourne le ou les Tweets correspondant.

La fonction `compare_two_images` permet de comparer deux images d'une méthode complétement différence de celle utilisée par le moteur CBIR. Cela permet de vérifier que les images trouvées par la recherche inversée sont bien les bonnes.


## Sous-modules

* `cbir_engine` : Moteur de recherche d'image par le contenu ("Content-Based Image Retrieval", CBIR), mais ne gère pas de base de données. Ce moteur est généraliste, il peut donc être réutilisé dans un autre projet, à condition de réécrire un accès à une base de données et l'itération sur cette base (Pour la recherche).
* `database` : Couche d'abstraction à l'utilisation de la base de données. Cette couche est spécialisée pour notre projet.
* `twitter` : Couche d'abstraction à l'utilisation de l'API Twitter via la librairie Python Tweepy. Est spécialisé, contient uniquement les fonctions dont nous avons besoin.
* `utils` : Divers fonctions utiles.

Les classes présentes ici font le lien entre le moteur CBIR et la base de données, mais est spécialisé pour les images dans des Tweets.
