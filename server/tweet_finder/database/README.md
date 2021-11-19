# Module de la base de données pour le Tweet Finder

## Tables de la base de données

### Table `tweets`

Stocke les Tweets analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* `tweet_id BIGINT UNSIGNED PRIMARY KEY` : ID du Tweet,
* `image_1_name VARCHAR(19)` : Identifiant de la première image du Tweet,
* `image_1_hash BINARY(?)` : Empreinte de la première image (Avec ? déterminé par le moteur CBIR),
* `image_2_name VARCHAR(19)` : Identifiant de la deuxième image du Tweet,
* `image_2_hash BINARY(?)` : Empreinte de la deuxième image (Avec ? déterminé par le moteur CBIR),
* `image_3_name VARCHAR(19)` : Identifiant de la troisième image du Tweet,
* `image_3_hash BINARY(?)` : Empreinte de la troisième image (Avec ? déterminé par le moteur CBIR),
* `image_4_name VARCHAR(19)` : Identifiant de la quatrième image du Tweet,
* `image_4_hash BINARY(?)` : Empreinte de la quatrième image (Avec ? déterminé par le moteur CBIR).

Notes :
* Seules les Tweets avec au moins une image sont stockés.
* Un Tweet ne peut pas contenir plus de 4 images.
* Si une image est corrompue / perdue par Twitter, son nom est quand même stocké (Mais son empreinte est à `NULL`).
* Les identifiants et les empreintes peuvent être à `NULL` si il n'y a pas d'image en plus.

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
* `last_retry_date DATETIME` : Date locale de la dernière tentative d'indexation,
* `retries_count TINYINT UNSIGNED DEFAULT` : Compteur de tentatives de réindexation (0 par défaut).

### Avertissement : Réfléchir avant de vouloir stocker autre chose

AOTF ne stocke volontairement pas les associations entre les comptes Twitter et les comptes des artistes sur les sites supportés, ainsi que les illustrations de requêtes et leurs Tweets trouvés respectifs. En effet, ces données peuvent être très facilement changeantes, leur mise à jour reviendrait alors à refaire les mêmes opérations pour chaque requête. C’est pour cela qu’il ne faut **surtout pas** les stocker dans la base de données.

Il faut comprendre que ces associations sont du cache, et non des données "statiques". Ainsi, la seule possibilité pour optimiser le traitement est de les mettre en cache dans la mémoire partagée. Et c’est ce qui est actuellement fait pour les associations entre les illustrations et les Tweets, voir le module `shared_memory`.

**D'une manière générale, la base de données du serveur AOTF ne doit contenir que des données "statiques", c'est à dire qu'elles ne peuvent pas être modifiées.** Les seules exceptions sont pour :
* Les données des comptes Twitter analysées (Table `accounts`) : Leurs curseurs d'indexation, leurs dates de dernière mise à jour, et leurs dates de dernière utilisation, et leurs compteurs d'utilisations,
* Et les données pour les Tweets qui ont besoin d'être réindexés (Table `reindex_tweets`).

En effet, ce sont des données qui ont besoin de persistence lors d'un redémarrage du serveur AOTF. Elles s'opposent aux associations qui n'ont pas besoin de persistence, et encore moins d'être inclues dans une stratégie de sauvegarde.

## Objets dans ce module

### Classe `SQLite_or_MySQL`

Classe d'accès et de gestion de la base de données. Supporte SQLite ou MySQL. Utilise `parameters.py` pour choisir. Contient une multitude de mèthodes qu'on utilise dans "Artists on Twitter Finder".

### Classe `Image_in_DB`

Classe représentant une image dans la base de données. Ces objets sont renvoyés par l'itérateur de la fonction `get_images_in_db_iterator()` (`yield`). Contient les attributs suivants :
* `account_id` : L'ID du compte Twitter ayant posté cette image,
* `tweet_id` : L'ID du Tweet contenant l'image,
* `image_hash` : L'empreinte de l'image,
* `image_position` : La position de l'image dans le Tweet (1, 2, 3 ou 4).

Ces objets contiennent aussi un attribut `distance` qui est rempli par le moteur CBIR (Voir méthode `search_cbir()` de la classe `CBIR_Engine` dans le module [`cbir_engine`](../cbir_engine).

Utilisé par la classe `Reverse_Searcher` dans le thread de recherche inversée d'image (Module [`user_pipeline`](../../app/user_pipeline), procédure `thread_step_3_reverse_search`).
