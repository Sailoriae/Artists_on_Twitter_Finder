# Module de couche d'abstraction à la librairie Tweepy

Tweepy est la librairie utilisée pour accèder à l'API publique de Twitter.

L'objet `TweepyAbstraction` est une couche d'abstraction adaptée à l'utilisation du serveur de l'API publique de Twitter. Elle permet aussi de gèrer les limites de taux ("rate limits") de cette API.

Fonctions disponibles :

* `get_tweet( tweet_id )` :
  Retourne le Tweet avec l'ID entré en paramètre, sous la forme d'un objet `Status` de la librairie Tweepy. En effet, les Tweets dans Tweepy sont représentés par des objets `Status`. Retourne None si le Tweet est inexistant.

* `get_account_id( account_name, invert_mode = False )` :
  Retourne l'ID du compte Twitter dont le nom d'utilisateur (C'est à dire ce qu'il y a après le "@", par exemple "jack" pour "@jack", aussi appelé "screen name") est celui entré en paramètre. Ou None si l'utilisateur est introuvable.
  Peut aussi fonctionner en sens inverse si le paramètre optionnel `invert_mode` est à `True` : Retourne le nom d'utilisateur du compte Twitter dont l'ID est celui passé en paramètre, à la place de `account_name`.

* `get_account_tweets( account_id, since_tweet_id = None )` :
  Retourne l'itérateur des Tweets du compte Twitter dont l'ID est celui passé en paramètre. Cette itération commence au Tweet le plus récent, est va jusqu'au Tweet avec l'ID `since_tweet_id`, ou jusqu'à 3 200 Tweets maximum.
  En effet, aucune API Twitter ne peut retourner plus de 3 200 Tweets vers le passé pour un utilisateur.
  Cette fonction filtre les Retweets, mais ils sont quand même comptés dans les 3 200 Tweets maximum.