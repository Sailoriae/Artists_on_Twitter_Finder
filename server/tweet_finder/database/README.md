# Module de la base de données pour le Tweet Finder

## Tables de la base de données

### Table `tweets`

Stocke les Tweets analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* `tweet_id BIGINT UNSIGNED PRIMARY KEY` : ID du Tweet,
* `hashtags TEXT` : Liste des hashtags du Tweet, avec le croisillon "#", séparés par des points-virgules ";",

Notes :
* Seules les Tweets avec au moins une image sont stockés.
* Un Tweet ne peut pas contenir plus de 4 images.
* Si une image est corrompue / perdue par Twitter, on la stocke quand même, en remplissant sa liste de caractéristiques par des `NULL`.

### Table `tweets_images_1`

Stocke la première image des Tweets analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* 240 colonnes `image_1_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la première image du Tweet,.

### Table `tweets_images_2`

Stocke la deuxième image des Tweets analysés, si il y en a une. Sinon, l'ID du Tweet n'apparait pas dans cette table.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* 240 colonnes `image_2_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la deuxième image du Tweet.

### Table `tweets_images_3`

Stocke la troisième image des Tweets analysés, si il y en a une. Sinon, l'ID du Tweet n'apparait pas dans cette table.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* 240 colonnes `image_3_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la troisième image du Tweet.

### Table `tweets_images_4`

Stocke la quatrième image des Tweets analysés, si il y en a une. Sinon, l'ID du Tweet n'apparait pas dans cette table.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED` : ID du compte Twitter ayant posté le Tweet,
* 240 colonnes `image_4_features_i FLOAT UNSIGNED` (i allant de 0 à 239 compris) : Liste des caractéristiques de la quatrième image du Tweet.

### Table `accounts`

Stocke les comptes Twitter analysés.

Contient les attributs suivants :
* `account_id BIGINT UNSIGNED PRIMARY KEY` : L'ID du compte Twitter,
* `last_SearchAPI_indexing_api_date CHAR(10)` : La date du dernier scan de ce compte avec l'API de recherche, au format YYYY-MM-DD (A donner au prochain scan pour éviter de rescanner tous les Tweets du compte),
* `last_SearchAPI_indexing_local_date DATETIME` : La date locale de la dernière mise à jour avec l'API de recherche, utilisé uniquement par le thread de mise à jour automatique,
* `last_TimelineAPI_indexing_tweet_id BIGINT UNSIGNED` : L'ID du tweet le plus récent de ce compte scanné avec l'API de timeline (A donner au prochain scan pour éviter de rescanner tous les Tweets du compte),
* `last_TimelineAPI_indexing_local_date DATETIME` : La date locale de la dernière mise à jour avec l'API de timeline, utilisé uniquement par le thread de mise à jour automatique.
* `last_use DATETIME` : La date locale de la dernière recherche inversée sur ce compte.
* `uses_count BIGINT UNSIGNED DEFAULT 0` : Compteur de recherches inversées sur ce compte.

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

### Classe `Less_Recently_Updated_Accounts_Iterator`

Renvoyé par la méthode `get_images_in_db_iterator()` de la classe `SQLite_or_MySQL`. Itère sur tous les comptes Twitter stockés dans la base de données, classés dans l'ordre de clui qui a la date de mise à jour locale la plus vielle. Cette date correspond à la plus vielle des attributs `last_TwitterAPI_indexing_tweet_id` et `last_TwitterAPI_indexing_local_date`. Si un de ces deux attributs est à `NULL`, leur compte correspondant sera donné en premier !

Itère des triplets contenant dans cet ordre :
* L'ID du compte Twitter,
* La date locale de la dernière mise à jour avec l'API de recherche,
* La date locale de la dernière mise à jour avec l'API de timeline.

Utilisé par le thread de mise à jour automatique (Procédure `thread_auto_update_accounts`).

### Fonction `features_list_for_db`

Permet de forcer la taille d'une liste Python en la coupant ou la ralongeant avec des `None`. N'est pas utilisée, puisque le moteur CBIR renvoir des listes fixes de 240 valeurs ! Cette taille de 240 valeurs est définie à l'initialisation de la classe `CBIR_Engine`.
Si cette valeur est changée, il faut :
* Réintialiser la base de données ! Ou recalculer la liste des caractéristiques pour tous les Tweets,
* Modifier la constante `CBIR_LIST_LENGHT` dans tous les fichiers de ce module `database`.

### Dictionnaire `sql_requests_dict`

Dictionnaire de requêtes SQL pré-fabriquées à l'initialisation.
