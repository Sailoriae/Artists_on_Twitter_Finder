# Artists on Twitter Finder : Client

## Classe `WebAPI_Client`

Cette classe gère la connexion au serveur "Artists on Twitter Finder".
Après son utilisation, il faut vérifier que son attribut `ready` soit à `True`. Il indique que la connexion au serveur a réussi.

Elle contient les mèthode publique suivantes :

* `get_request( illust_url : str ) -> dict`
  Retourne le JSON (Fonctionne comme un dictionnaire Python) renvoyé par le serveur pour l'illustration dont l'URL est passée en paramètre.
  Ou retourne `None` si il y a eu un problème.

* `get_request( get_twitter_accounts : str ) -> dict`
  Retourne la liste des comptes Twitter trouvés pour l'artiste de l'illustration dont l'URL est passée en paramètre, sous la forme d'une liste dictionnaires contenant les clés suivantes :
  - `account_name` : Le nom du compte Twitter, par exemple : `jack` pour "@jack",
  - `account_id` : L'ID de ce compte Twitter.
  Ou retourne une liste vide si aucun compte Twitter n'a été trouvé.
  Ou retourne `None` si il y a eu un problème, ou que le temps de timeout s'est écoulé. Ce temps est de 300 par défaut, et peut-être modifié avec le paramètre optionnel `timeout`.

* `get_request( get_tweets : str ) -> dict`
  Retourne la liste des Tweets de l'artiste contenant l'illustration dont l'URL est passée en paramètre, sous la forme d'une liste de dictionnaires contenant les clés suivantes :
  - `tweet_id` : L'ID du Tweet,
  - `account_id` : L'ID du compte Twitter qui a posté ce Tweet,
  - `image_position` : La position de l'image dans le tweet, entre 1 et 4,
  - `distance` : La distance calculée entre l'image de requête et cette image.
  Ou retourne une liste vide si aucun compte Twitter n'a été trouvé.
  Ou retourne `None` si il y a eu un problème, ou que le temps de timeout s'est écoulé. Ce temps est de 3600 par défaut, et peut-être modifié avec le paramètre optionnel `timeout`.


Ces mèthodes peuvent émettre les exceptions suivantes :

* `Server_Connection_Not_Initialised` : La connexion au serveur n'a pas été intialisée correctement.

* `Max_Pending_Requests_On_Server` : Une nouvelle requête n'a pas pue être créée sur le serveur car l'adresse IP du client a atteint son maximum de requêtes en cours de traitement sur le serveur.


## Script `example_scan_danbooru_tag.py`

Permet de remplir la base de données du serveur avec les comptes Twitter des artistes d'un tag Danbooru.


## Script `example_scan_deviantart_home.py`

Permet de remplir la base de données du serveur avec les comptes Twitter des illustrations présentes sur la page d'acceuil de DeviantArt.
