# Pipeline de traitement dans `app.py`

Une requête est représentée par un objet `Request`, et est identifiée par son URL de requête, c'est à dire l'URL de l'illustration sur un site supporté.

La classe `Pipeline` doit être instanciée une seule fois : C'est la mémoire partagée entre les classes. Elle contient notamment les files d'attentes et la liste `requests`.

Toutes les requêtes qui font le parcours complet sont dans la liste `requests` de l'objet `Pipeline`, et seulement ces requêtes. Comme les objets Python sont passés par addresse, ils sont en même dans dans une des queue si ils sont en cours de traitement.

Voici les 5 étapes de traitement d'une requête :

1. Link Finder : Vérification de l'URL, recherche de l'image source, et recherche de comptes Twitter.
   * File d'attente : `step_1_link_finder_queue`
   * Procédure du thread de traitement : `thread_step_1_link_finder`
   * ID et nom du status : `1`, `LINK_FINDER`

2. Listage des tweets d'un compte avec GetOldTweets3.
   * File d'attente : `step_2_GOT3_list_account_tweets_queue`
   * Procédure du thread de traitement : `thread_step_2_GOT3_list_account_tweets`
   * ID et nom du status : `3`, `LIST_ACCOUNT_TWEETS`
   * Il ne peut y avoir qu'un seul thread pour cette étape !

3. Indexation des tweets trouvés par GetOldTweets3 : Détection d'images, calcul de la liste des caractéristiques avec le moteur CBIR, stockage dans la base de données.
   * File d'attente : `step_3_GOT3_index_account_tweets_queue`
   * Procédure du thread de traitement : `thread_step_3_GOT3_index_account_tweets`
   * ID et nom du status : `5`, `INDEX_ACCOUNT_TWEETS`
   * Il ne peut y avoir qu'un seul thread pour cette étape !

L'indexation par GOT3 est séparée en deux partie car ce n'est pas un itérateur.

4. Indexation des tweets avec l'API publique de Twitter : Détection d'images, calcul de la liste des caractéristiques avec le moteur CBIR, stockage dans la base de données.
   * File d'attente : `step_4_TwitterAPI_index_account_tweets_queue`
   * Procédure du thread de traitement : `thread_step_4_TwitterAPI_index_account_tweets`
   * ID et nom du status : `7`, `SECOND_INDEX_ACCOUNT_TWEETS`
   * Il ne peut y avoir qu'un seul thread pour cette étape !
   * Cette indexation est totalement indépendante de l'indexation avec GetOldTweets3, même si on revoit passer les mêmes Tweets.

Pour tous les threads d'indexation, avant de passer au calcul de la liste des caractéristiques, on vérifie avant que le Tweet n'est pas déjà dans la base de données.

5. Recherche inversée d'image.
   * File d'attente : `step_5_reverse_search_queue`
   * Procédure du thread de traitement : `thread_step_5_reverse_search`
   * ID et nom du status : `9`, `IMAGE_REVERSE_SEARCH`

A tout moment, on peut connaitre le status d'une requête via la CLI dans le processus principal, ou via l'API, gérée par le thread `http_server_thread_main`.
Lorsque la procédure est terminée, on peut aussi voir son résultat.

Voir `API_HTTP.md` pour plus d'informations.

Il est possible que des requêtes soient indépendantes, afin d'effectuer une action précise, comme le scan d'un compte Twitter (Lancé par le thread de mise à jour automatique), ou la recherche d'image inversé dans toute la base de données. Elles ne sont disponibles que depuis la CLI, et ne sont pas indexées dans la liste `requests`.
