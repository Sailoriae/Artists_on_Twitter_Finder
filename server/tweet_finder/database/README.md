# Module de la base de données pour le Tweet Finder

## Tables de la base de données

### Table `tweets`

Stocke les Tweets analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* `tweet_id BIGINT UNSIGNED PRIMARY KEY` : ID du Tweet,
* `hashtags TEXT` : Liste des hashtags du Tweet, avec le croisillon "#", séparés par des points-virgules ";".

Notes :
* Seules les Tweets avec au moins une image sont stockés.
* Un Tweet ne peut pas contenir plus de 4 images.
* Si une image est corrompue / perdue par Twitter, on la stocke quand même, en remplissant sa liste de caractéristiques par des `NULL`.

### Table `tweets_images_1`

Stocke la première image des Tweets analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du Tweet associé,
* 240 colonnes `image_1_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la première image du Tweet,.

### Table `tweets_images_2`

Stocke la deuxième image des Tweets analysés, si il y en a une. Sinon, l'ID du Tweet n'apparait pas dans cette table.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du Tweet associé,
* 240 colonnes `image_2_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la deuxième image du Tweet.

### Table `tweets_images_3`

Stocke la troisième image des Tweets analysés, si il y en a une. Sinon, l'ID du Tweet n'apparait pas dans cette table.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du Tweet associé,
* 240 colonnes `image_3_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la troisième image du Tweet.

### Table `tweets_images_4`

Stocke la quatrième image des Tweets analysés, si il y en a une. Sinon, l'ID du Tweet n'apparait pas dans cette table.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du Tweet associé,
* 240 colonnes `image_4_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la quatrième image du Tweet.

### Table `accounts`

Stocke les comptes Twitter analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED PRIMARY KEY` : L'ID du compte Twitter,
* `last_SearchAPI_indexing_api_date CHAR(10)` : **Curseur d'indexation avec l'API de recherche**, c'est-à-dire la date du dernier scan de ce compte avec l'API de recherche, au format YYYY-MM-DD (A donner au prochain scan pour éviter de rescanner tous les Tweets du compte),
* `last_SearchAPI_indexing_local_date DATETIME` : La date locale de la dernière mise à jour avec l'API de recherche, utilisé uniquement par le thread de mise à jour automatique,
* `last_SearchAPI_indexing_cursor_reset_date DATETIME` : La date locale du dernier reset du curseur d'indexation avec l'API de recherche. En effet, comme l'indexation sur le moteur de recherche interne à Twitter est fluctuante, on peut donc de temps en temps (De l'ordre d'une fois par ans) re-lister tous les Tweets de ce compte.
* `last_TimelineAPI_indexing_tweet_id BIGINT UNSIGNED` : **Curseur d'indexation avec l'API de timeline**, c'est-à-dire l'ID du tweet le plus récent de ce compte scanné avec l'API de timeline (A donner au prochain scan pour éviter de rescanner tous les Tweets du compte),
* `last_TimelineAPI_indexing_local_date DATETIME` : La date locale de la dernière mise à jour avec l'API de timeline, utilisé uniquement par le thread de mise à jour automatique,
* `last_use DATETIME` : La date locale de la dernière recherche inversée sur ce compte,
* `uses_count BIGINT UNSIGNED DEFAULT 0` : Compteur de recherches inversées sur ce compte.

### Table `reindex_tweets`

Si un Tweet a une image dont l'analyse a échouée et que l'erreur n'est pas connue comme insolvable (Voir la fonction `get_tweet_image()`), son dictionnaire (Voir la fonction `analyse_tweet_json()`) est stocké ici.

Contient les attributs suivants :
* `tweet_id BIGINT UNSIGNED PRIMARY KEY` : ID du Tweet,
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* `image_1_url TEXT` : URL de la première image,
* `image_2_url TEXT` : URL de la deuxième image (`NULL` sinon),
* `image_3_url TEXT` : URL de la troisième image (`NULL` sinon),
* `image_4_url TEXT` : URL de la quatrième image (`NULL` sinon),
* `hashtags TEXT` : Liste des hashtags du Tweet, avec le croisillon "#", séparés par des points-virgules ";",
* `last_retry_date DATETIME` : Date locale de la dernière tentative d'indexation,
* `retries_count TINYINT UNSIGNED DEFAULT` : Compteur de tentatives de réindexation (0 par défaut).

## Objets dans ce module

### Classe `SQLite_or_MySQL`

Classe d'accès et de gestion de la base de données. Supporte SQLite ou MySQL. Utilise `parameters.py` pour choisir. Contient une multitude de mèthodes qu'on utilise dans "Artists on Twitter Finder".

### Classe `Image_Features_Iterator`

Renvoyé par la méthode `get_images_in_db_iterator()` de la classe `SQLite_or_MySQL`. Itére sur toutes les images de Tweets présentes dans la base de données. Itère des objets `Image_in_DB`.

### Classe `Image_in_DB`

Classe représentant une image dans la base de données. Ces objets sont renvoyés par l'itérateur `Image_Features_Iterator`. Contient les attributs suivants :
* `account_id` : L'ID du compte Twitter ayant posté cette image,
* `tweet_id` : L'ID du Tweet contenant l'image,
* `image_features` : La liste des caractéristiques de l'image,
* `image_position` : La position de l'image dans le Tweet (1, 2, 3 ou 4).

Ces objets contiennent aussi un attribut `distance` qui est rempli par le moteur CBIR (Voir méthode `search_cbir` de la classe `CBIR_Engine` dans le module `cbir_engine`).

Utilisé par la classe `CBIR_Engine_with_Database` dans le thread de recherche inversée d'image (Module `user_pipeline`, procédure `thread_step_3_reverse_search`).

### Fonction `features_list_for_db`

Permet de forcer la taille d'une liste Python en la coupant ou la ralongeant avec des `None`. N'est pas utilisée, puisque le moteur CBIR renvoir des listes fixes de 240 valeurs ! Cette taille de 240 valeurs est définie à l'initialisation de la classe `CBIR_Engine`.
Si cette valeur est changée, il faut :
* Réintialiser la base de données ! Ou recalculer la liste des caractéristiques pour tous les Tweets,
* Modifier la constante `CBIR_LIST_LENGHT` dans tous les fichiers de ce module `database`.

### Dictionnaire `sql_requests_dict`

Dictionnaire de requêtes SQL pré-fabriquées à l'initialisation.
