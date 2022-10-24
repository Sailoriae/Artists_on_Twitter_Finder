# Tweet Finder

Le Tweet Finder est l'une des deux grandes parties du serveur "Artists on Twitter Finder", avec le [Link Finder](../link_finder).

Les classes `Tweets_Lister_with_SearchAPI` et `Tweets_Lister_with_TimelineAPI` listent les Tweets de comptes Twitter à partir du dernier scan (Ou tous les Tweet si le compte n'a pas été encore scanné) :
* `Tweets_Lister_with_SearchAPI` utilise la librairie SNScraper pour l'API Twitter utilisée par l'UI web https://twitter.com/search,
* Et `Tweets_Lister_with_TimelineAPI` utilise aussi la librairie SNScraper pour l'API Twitter utilisée par l'UI web d'un profil.
Elles utilisent une couche d'abstraction disponibles dans le module [`twitter`](twitter).

La classe `Tweets_Indexer` indexe les Tweets trouvés par les classes de listage :
1. Calcul de l'empreinte de chaque image de chaque Tweet, module [`cbir_engine`](cbir_engine), via la classe `Tweets_Indexer`,
2. Stockage ce dans la base de données en les associants à l'ID du Tweet, et l'ID du compte l'ayant Tweeté, module [`database`](database).

L'étape de listage communique ses Tweets trouvés à l'étape d'indexation via un objet `queue.Queue` (File d'attente), permettant de paralléliser ces deux étapes.
Cet objet est stocké dans le pipeline de traitement des requêtes de scan (Objet `Scan_Requests_Pipeline`) de la mémoire partagée.
Les Tweets sont insérés dans cette file sous la forme de dictionnaires, créés par la fonction `analyse_tweet_json()` à partie des JSON des Tweets renvoyés par les API de Twitter.
On peut aussi créer ces dictionnaires à partir des résultats de l'API v2 de Twitter via Tweepy, grâce à la fonction `analyse_tweepy_response()`.

Les étapes de listage peuvent aussi communiquer avec les Tweets des instructions d'enregistrement des curseurs. Ces instructions peuvent aussi permettre de mettre fin à la requête de scan d'un compte Twitter (Comment la classe `Tweets_Indexer` les utilise). Il est **très** important que les curseurs soient enregistrés à la fin de l'indexation de tous les Tweets trouvés par l'étape de listage. Cela permet d'avoir une base de données cohérente en cas d'extinction du serveur.

La classe `Reverse_Searcher` permet de rechercher un Tweet à partir d'une image, et éventuellement du compte Twitter sur lequel chercher :
1. Calcul de l'empreinte de l'image de recherche, module [`cbir_engine`](cbir_engine),
2. Obtient l'itérateur sur la base de données, module [`database`](database),
3. Calcul la distance entre l'image de requête et chaque image de l'itérateur, module [`cbir_engine`](cbir_engine),
4. Retourne le ou les Tweets correspondant.

Cette classe permet aussi de faire une recherche exacte, c'est à dire que les images retournées ont exactement la même empreinte que l'image de requête. Cela permet d'être plus rapide, mais mène à un peu moins de 10% de faux-négatifs (C'est à dire des images identiques qui auraient dues être retournées). Cette statistique a été trouvée via l'analyse des résultats par la recherche classique (Voir le script `../../misc/analyze_results.py`).


## Sous-modules

* [`cbir_engine`](cbir_engine) : Moteur de recherche d'image par le contenu ("Content-Based Image Retrieval", CBIR), mais ne gère pas de base de données. Ce moteur est généraliste, il peut donc être réutilisé dans un autre projet, à condition de réécrire un accès à une base de données et l'itération sur cette base (Pour la recherche).
* [`database`](database) : Couche d'abstraction à l'utilisation de la base de données. Cette couche est spécialisée pour notre projet.
* [`twitter`](twitter) : Couche d'abstraction à l'utilisation des librairies Python qui permettent d'accéder aux API de Twitter. Est spécialisée, contient uniquement les fonctions dont nous avons besoin.
* [`utils`](utils) : Divers fonctions utiles.

Les classes présentes ici font le lien entre le moteur CBIR et la base de données, mais est spécialisé pour les images dans des Tweets.
