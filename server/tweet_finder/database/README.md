# Module de la base de données pour le Tweet Finder

## Tables de la base de données

### Table `tweets`

Stocke les Tweets analysés.

Contient les attributs suivants :
* `account_id INTEGER` : ID du compte Twitter ayant posté le Tweet,
* `tweet_id INTEGER PRIMARY KEY` : ID du Tweet,
* `image_1_features TEXT` : Liste des caractéristiques de la première image du Tweet,
* `image_2_features TEXT` : Liste des caractéristiques de la deuxième image du Tweet, ou NULL s'il n'y a pas de deuxième image,
* `image_3_features TEXT` : Liste des caractéristiques de la troisième image du Tweet, ou NULL s'il n'y a pas de troisième image,
* `image_4_features TEXT` : Liste des caractéristiques de la quatrième image du Tweet, ou NULL s'il n'y a pas de quatrième image,
* `hashtags TEXT` : Liste des hashtags du Tweet.

Note : Un Tweet ne peut pas contenir plus de 4 images.

Les listes sont stockées sous forme de chains de caractères. Chaque élément est séparé par un point-virgule(`;`).

### Table `accounts`

Stocke les comptes Twitter analysés.

Contient les attributs suivants :
* `account_id INTEGER PRIMARY KEY` : L'ID du compte Twitter,
* `last_GOT3_indexing_api_date STRING` : La date du dernier scan avec GetOldTweets3 de ce compte, au format YYYY-MM-DD (A donner au prochain scan pour éviter de rescanner tous les Tweets du compte),
* `last_GOT3_indexing_local_date TIMESTAMP` : Le timestamp de la dernière modification de l'attribut précédent, utilisé uniquement par le thread de mise à jour automatique,
* `last_TwitterAPI_indexing_tweet_id INTEGER` : L'ID du tweet le plus récent de ce compte scanné avec Tweepy (A donner au prochain scan pour éviter de rescanner tous les Tweets du compte),
* `last_TwitterAPI_indexing_local_date TIMESTAMP` : Le timestamp de la dernière modification de l'attribut précédent, utilisé uniquement par le thread de mise à jour automatique.
