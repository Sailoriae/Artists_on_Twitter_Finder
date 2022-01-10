# Couche d'abstraction à l'utilisation des API de Twitter

## Couche d'abstraction à la librairie Tweepy

Tweepy est la librairie utilisée pour accéder à l'API publique de Twitter.

L'objet `TweepyAbstraction` est une couche d'abstraction adaptée à l'utilisation du serveur de l'API publique de Twitter. Elle permet aussi de gérer les limites de taux ("rate limits") de cette API.

Fonctions disponibles :

* `get_tweet( tweet_id )` :
  Retourne le Tweet avec l'ID entré en paramètre, sous la forme d'un objet `Status` de la librairie Tweepy. En effet, les Tweets dans Tweepy sont représentés par des objets `Status`. Retourne None si le Tweet est inexistant.

* `get_account_id( account_name, invert_mode = False )` :
  Retourne l'ID du compte Twitter dont le nom d'utilisateur (C'est à dire ce qu'il y a après le "@", par exemple "jack" pour "@jack", aussi appelé "screen name") est celui entré en paramètre. Ou None si le compte n'existe pas, est désactivé, suspendu, ou privé.
  Peut aussi fonctionner en sens inverse si le paramètre optionnel `invert_mode` est à `True` : Retourne le nom d'utilisateur du compte Twitter dont l'ID est celui passé en paramètre, à la place de `account_name`.

* `get_multiple_accounts_ids ( accounts_names )` :
  Retounre une liste de tuples contenant le nom du compte, et son ID, correspondant à la liste de nom de comptes passée en paramètre. Si un compte n'existe pas, est désactivé, suspendu, ou privé, il ne figure pas dans la liste de retour.

* `get_account_tweets( account_id, since_tweet_id = None )` :
  Retourne l'itérateur des Tweets du compte Twitter dont l'ID est celui passé en paramètre. Cette itération commence au Tweet le plus récent, est va jusqu'au Tweet avec l'ID `since_tweet_id`, ou jusqu'à 3 200 Tweets maximum.
  En effet, aucune API Twitter ne peut retourner plus de 3 200 Tweets vers le passé pour un utilisateur.
  Cette fonction filtre les Retweets, mais ils sont quand même comptés dans les 3 200 Tweets maximum.

* `blocks_me( account_id )` :
  Retourne `True` si l'utilisateur dont l'ID passé en paramètre bloque l'utilisateur courant (Clés passées en paramètre à l'objet), `False` sinon.


## Couche d'abstraction à la librairie SNScrape

SNSCrape est la librairie utilisée pour accéder à l'API de recherche de Twitter, celle qui ne nous limite pas à 7 jours et ne nous demande pas de payer. Pour faire simple : Celle qui est utilisable pour un projet qui ne rapporte rien et a besoin d'avoir plus de 3 200 Tweets par comptes.

L'objet `SNScrapeAbstraction` est une couche d'abstraction adaptée à l'utilisation du serveur de cette API. Elle permet aussi dé gérer les erreurs HTTP 429, c'est à dire les limites de taux.

Fonctions disponibles :

* `search( self, query : str, output_function = print )` :
  Exécute la recherche `query`, et donne les JSON des Tweets à la fonction `output_function()`. Tous les Tweets de cette recherche sont retournés !
