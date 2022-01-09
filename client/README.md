# Artists on Twitter Finder : Client

## Classe `AOTF_Client`

Cette classe gère la connexion à l'API du serveur AOTF.

### Constructeur

```python
__init__ ( base_api_address : str = "http://localhost:3301/", ignore_check : bool = False ) -> None
```

Prend en entrée les paramètres suivants :
- `base_api_address` : Adresse de la racine de l'API du serveur AOTF. Elle peut être par exemple `http://localhost:3301/`, ou `https://sub.domain.tld/api/`.
- `ignore_check` : Sauter la vérification de la connexion au serveur. Peut être utile en production.

Reut émettre une exception `Error_During_Server_Connection_Init` en cas d'échec de la connexion au serveur (Uniquement si `ignore_check = False`).

### Méthode `get_request()`

```python
get_request ( illust_url : str ) -> dict
```

Prend en entrée le paramètre suivant :
- `illust_url` : URL de l'illustration à traiter. Elle doit mener à une page d'une illustration sur un site supporté par le serveur AOTF.

Retourne le JSON (Fonctionne comme un dictionnaire Python) renvoyé par le serveur pour l'illustration dont l'URL est passée en paramètre. Pour connaitre exactement le contenu de ce dictionnaire, voir la documentation de l'API pour l'endpoint `GET /query` dans le fichier [`../doc/API_HTTP.md`](../doc/API_HTTP.md).

### Méthode `get_twitter_accounts()`

```python
get_twitter_accounts ( get_twitter_accounts : str, timeout = 300 ) -> dict
```

Prend en entrée les paramètres suivants :
- `illust_url` : URL de l'illustration à traiter.
- `timeout` : Temps d'attente maximal avant émission d'une exception `Timeout_Reached`.

Retourne la liste des comptes Twitter trouvés pour l'artiste de l'illustration dont l'URL est passée en paramètre, sous la forme d'une liste dictionnaires contenant les clés suivantes :
- `account_name` : Le nom du compte Twitter, par exemple : `jack` pour "@jack",
- `account_id` : L'ID de ce compte Twitter.

Peut retourner une liste vide si aucun compte Twitter n'a été trouvé. Ou `None` s’il y a eu un problème sur le serveur AOTF. Pour plus de précision, il faut obtenir le JSON renvoyé par la méthode `get_request()`.

### Méthode `get_tweets()`

```python
get_tweets ( get_tweets : str, timeout = 3600 ) -> dict
```

Prend en entrée les paramètres suivants :
- `illust_url` : URL de l'illustration à traiter.
- `timeout` : Temps d'attente maximal avant émission d'une exception `Timeout_Reached`.

Retourne la liste des Tweets de l'artiste contenant l'illustration dont l'URL est passée en paramètre, sous la forme d'une liste de dictionnaires contenant les clés suivantes :
- `tweet_id` : L'ID du Tweet,
- `account_id` : L'ID du compte Twitter,
- `image_position` : Chaine contenant la position de l'image dans le tweet et le nombre d'images dans le Tweet, entre 1 et 4,
- `distance` : Le nombre de bits de différence entre l'empreinte de l'image de requête et celle de l'image trouvée.

Elle peut retourner une liste vide si aucun compte Twitter n'a été trouvé. Ou `None` si il y a eu un problème sur le serveur AOTF.

### Exceptions

Ces trois méthodes peuvent émettre les exceptions suivantes :

* `Server_Connection_Not_Initialised` : La connexion au serveur n'a pas été initialisée correctement. Cela arrive uniquement lorsqu'une exception `Error_During_Server_Connection_Init` a été émise lors de l'initialisation de la classe.

* `Max_Processing_Requests_On_Server` : Une nouvelle requête n'a pas pu être créée sur le serveur car l'adresse IP du client a atteint son maximum de requêtes en cours de traitement sur le serveur.

* `Timeout_Reached` : Le temps d'attente maximal précisé par le paramètre `timeout` a été atteint.


## Scripts d'exemples

* `example_scan_danbooru_tag.py`
  Permet de remplir la base de données du serveur avec les comptes Twitter des artistes d'un tag Danbooru.

* `example_scan_deviantart_home.py`
  Permet de remplir la base de données du serveur avec les comptes Twitter des artistes présents sur la page d'accueil de DeviantArt.

* `example_scan_deviantart_search.py`
  Permet de remplir la base de données du serveur avec les comptes Twitter des artistes d'une recherche sur DeviantArt.
  Utilise la fonction utilisé pour le script `example_scan_deviantart_home.py`.

* `example_scan_derpibooru_search.py`
  Permet de remplir la base de données du serveur avec les comptes Twitter des artistes d'une recherche sur Derpibooru.
