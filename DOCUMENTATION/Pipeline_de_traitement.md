# Pipeline de traitement dans `app.py`

Une requête est représentée par un objet `Request`.

Une requête est identifiée par son URL de requête.

Toutes les requêtes qui font le parcours complet sont dans la liste `requests`. Comme les objets Python sont passés par addresse, ils sont en même dans dans une des queue si ils sont en cours de traitement.

Voici les 4 étapes de traitement d'une requête :

1. Link Finder : Vérification de l'URL, recherche de l'image source, et recherche de comptes Twitter.
   * File d'attente : `link_finder_queue`
   * Procédure du thread de traitement : `link_finder_thread_main`
   * ID et nom du status : `1`, `LINK_FINDER`

2. Listage des tweets d'un compte avec GetOldTweets3.
   * File d'attente : `list_account_tweets_queue`
   * Procédure du thread de traitement : `list_account_tweets_thread_main`
   * ID et nom du status : `1`, `LIST_ACCOUNT_TWEETS`
   * Il ne peut y avoir qu'un seul thread pour cette étape !

3. Indexation des tweets trouvés par GetOldTweets3 : Détection d'images, calcul de la liste des caractéristiques avec le moteur CBIR, stockage dans la base de données.
   * File d'attente : `index_twitter_account_queue`
   * Procédure du thread de traitement : `index_twitter_account_thread_main`
   * ID et nom du status : `1`, `INDEX_ACCOUNT_TWEETS`
   * Il ne peut y avoir qu'un seul thread pour cette étape !

4. Recherche inversée d'image.
   * File d'attente : `reverse_search_queue`
   * Procédure du thread de traitement : `reverse_search_thread_main`
   * ID et nom du status : `1`, `IMAGE_REVERSE_SEARCH`

A tout moment, on peut connaitre le status d'une requête via la CLI dans le processus principal, ou via l'API, gérée par le thread `http_server_thread_main`.
Lorsque la procédure est terminée, on peut aussi voir son résultat.

Voir `API_HTTP.md` pour plus d'informations.

Il est possible que des requêtes soient indépendantes, afin d'effectuer une action précise. Elles ne sont disponibles que depuis la CLI, ne sont pas indexées dans la liste `requests`, et ne passent que par une seule file d'attente, et donc un seul thread.
