# Module de la base de données pour le Tweet Finder

## Tables de la base de données

### Table `tweets`

Stocke les Tweets analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* `tweet_id BIGINT UNSIGNED PRIMARY KEY` : ID du Tweet,
* `hashtags TEXT` : Liste des hashtags du Tweet, séparés par des ";",
* 240 colonnes `image_1_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la première image du Tweet,
* 240 colonnes `image_2_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la deuxième image du Tweet, ou NULL s'il n'y a pas de deuxième image,
* 240 colonnes `image_3_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la troisième image du Tweet, ou NULL s'il n'y a pas de troisième image,
* 240 colonnes `image_4_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la quatrième image du Tweet, ou NULL s'il n'y a pas de quatrième image.

Note : Un Tweet ne peut pas contenir plus de 4 images.

### Table `accounts`

Stocke les comptes Twitter analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED PRIMARY KEY` : L'ID du compte Twitter,
* `last_GOT3_indexing_api_date CHAR(10)` : La date du dernier scan avec GetOldTweets3 de ce compte, au format YYYY-MM-DD (A donner au prochain scan pour éviter de rescanner tous les Tweets du compte),
* `last_GOT3_indexing_local_date DATETIME` : Le timestamp de la dernière modification de l'attribut précédent, utilisé uniquement par le thread de mise à jour automatique,
* `last_TwitterAPI_indexing_tweet_id BIGINT UNSIGNED` : L'ID du tweet le plus récent de ce compte scanné avec Tweepy (A donner au prochain scan pour éviter de rescanner tous les Tweets du compte),
* `last_TwitterAPI_indexing_local_date TIMESTAMP` : Le timestamp de la dernière modification de l'attribut précédent, utilisé uniquement par le thread de mise à jour automatique.
