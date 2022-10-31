# Couche d'abstraction à l'utilisation des API de Twitter

## Couche d'abstraction à la librairie Tweepy

Tweepy est la librairie utilisée pour accéder à l'API publique de Twitter.

L'objet `TweepyAbstraction` est une couche d'abstraction adaptée à notre utilisation de l'API publique de Twitter. Elle permet aussi de gérer les limites de taux ("rate limits") de cette API. Certaines de ses méthodes peuvent utiliser l'API v2 (Paramètre `use_api_v2`), mais il faut que l'application ait accès à cette nouvelle API.

Lors qu'une méthode retourne des Tweets, ils sont retournés sous la forme d'objets `Status` de la librairie Tweepy. Ces objets ont un attribut `_json` contenant le dictionnaire de l'objet JSON représentant un Tweet, retournée par l'API Twitter. Dans le cas d'un appel sur l'API v2 (`use_api_v2 = True`), les Tweets sont regroupés sous la forme d'objets `Responses`, contenant notamment un attribut `data` (Liste des Tweets), et un attribut `includes.media` (Médias associés aux Tweets).

Lorsqu'une méthode demande un nom d'utilisateur, on parle de ce qu'il y a paèrs le `@`, par exemple `jack`. Ceci s'appelle le "screen name", mais on n'utilise ce terme nulle part dans le serveur AOTF.

Méthodes disponibles :

* `get_tweet( tweet_id, use_api_v2 = False )` :
  Retourne le Tweet ID `tweet_id`, ou `None` si il est inexistant (Ou inaccessible).

* `get_multiple_tweets( tweets_ids, use_api_v2 = False )` :
  Retourne une liste des Tweets dont leurs IDs ont étés demandés dans `tweets_ids`. Si un Tweet n'existe pas (Ou est inaccessible), il ne sera pas retourné.
  Retourne une liste d'objets `Response` si est utilisée avec l'API v2.

* `get_account_id( account_name, invert_mode = False )` :
  Retourne l'ID du compte Twitter dont le nom d'utilisateur est celui entré en paramètre. Ou `None` si le compte n'existe pas, est désactivé, suspendu, ou privé.
  Peut aussi fonctionner en sens inverse si le paramètre optionnel `invert_mode` est à `True` : Retourne le nom d'utilisateur du compte Twitter dont l'ID est celui passé en paramètre, à la place de `account_name`.

* `get_multiple_accounts_ids ( accounts_names )` :
  Retourne une liste de tuples contenant le nom d'utilisateur, et son ID, correspondant à la liste de nom de comptes passée en paramètre. Si un compte n'existe pas, est désactivé, suspendu, ou privé, il ne figure pas dans la liste de retour.

* `get_account_tweets( account_id, since_tweet_id = None, use_api_v2 = False )` :
  Retourne l'itérateur des Tweets du compte Twitter dont l'ID est celui passé en paramètre. Cette itération commence au Tweet le plus récent, est va jusqu'au Tweet avec l'ID `since_tweet_id`, ou jusqu'à 3 200 Tweets maximum.
  En effet, aucune API Twitter ne peut retourner plus de 3 200 Tweets vers le passé pour un utilisateur.
  Cette fonction demande à l'API de ne pas retourner les Retweets, mais ils sont quand même comptés dans les 3 200 Tweets maximum.
  Retourne une liste d'objets `Response` si est utilisée avec l'API v2. Cependant, il vaut mieux éviter d'utiliser cette méthode sur l'API v2, puisque les Tweets reçus sont comptés dans le "Tweet Cap" mensuel (500k ou 2M de Tweets, c'est très peu).

* `blocks_me( account_id )` :
  Retourne `True` si l'utilisateur dont l'ID passé en paramètre bloque l'utilisateur courant (Clés passées en paramètre à l'objet), `False` sinon.


## Couche d'abstraction à la librairie SNScrape

SNSCrape est la librairie utilisée pour accéder à l'API de recherche de Twitter, celle qui ne nous limite pas à 7 jours et ne nous demande pas de payer. Pour faire simple : Celle qui est utilisable pour un projet qui ne rapporte rien et a besoin d'avoir plus de 3 200 Tweets par comptes.

Les Tweets sont retournés sous la forme d'objets `Tweet` de la librairie SNScrape. Notre modification de cette librairie leur ajoute un attribut `_json` contenant le dictionnaire de l'objet JSON représentant un Tweet, retournée par l'API Twitter. Attention, comme SNScrape utilise des API privées, ce JSON peut changer de forme.

L'objet `SNScrapeAbstraction` est une couche d'abstraction adaptée à l'utilisation du serveur de cette API. Elle permet aussi de gérer les erreurs HTTP 429, c'est à dire les limites de taux.

Méthodes disponibles :

* `search( self, query : str )` :
  Retourne un itérateur de Tweets en exécutant recherche `query`. Tous les Tweets de cette recherche sont retournés !

* `user_tweets( self, account_id, since_tweet_id = None )` :
  Retourne un itérateur des Tweets publiés par un compte (Via son ID ou son nom d'utilisateur, faire attention au type). Seuls les 3 200 premiers Tweets seront retournés. De plus, certains peuvent manquer, notamment dans les longs threads (Ils sont coupés au-delà de 3 Tweets). Il vaut mieux donc éviter de l'utiliser.

* `get_tweets( self, tweets_ids )` :
  Retourne une liste de Tweets obtenus via leurs IDs. Attention, cette méthode fait une requête par Tweet, elle est donc très lente. Il vaut mieux donc éviter de l'utiliser.
