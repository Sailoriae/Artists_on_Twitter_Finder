# Utilisation de l'API

Le serveur est utilisable via son serveur HTTP, depuis la même machine, ou l'extérieur, en faisant un proxy depuis Apache ou Nginx. Ne pas ouvrir le port du serveur !

Les requêtes sont indentifiées par leur URL (C'est à dire l'URL de l'illustration sur un des sites supportés). La méthode pour lancer une procédure ou obtenir le résultat est la même : `GET /query?url=[URL de l'illustration de requête]`

Par exemple : `GET /query?url=https://www.deviantart.com/serafleur/art/Sailor-Moon-604185347`

Le serveur répond par un JSON qui contient toujours les mêmes champs :
```
{
	"status" : "END",
	"has_first_time_scan" : true,
	"twitter_accounts" : [
		{
			"account_name" : "serafleur",
			"account_id" : "3064686505"
		}
	],
	"results" : [
		{
			"tweet_id" : 797039787534262272,
			"account_id" : 3064686505,
			"image_position" : "1/1",
			"distance" : 0
		}
	],
	"error" : null
}
```

La liste `twitter_accounts` contient les comptes Twitter identifiés comme étant ceux de l'artiste de l'illustration de requête.

La liste `results` contient les Tweets avec images trouvés, triée par le nombre de bits de différence avec l'empreinte de l'image de requête, puis si égalité par le nombre d'images dans le Tweet, puis si encore égalité par l'ID du Tweet. Le premier élément de cette liste est donc le Tweet contenant l'image la plus proche.

Liste des attributs d'un résultat dans la liste `results` :
- `tweet_id` : L'ID du Tweet.
- `account_id`: L'ID du compte Twitter.
- `image_position` : Chaine contenant la position de l'image dans le tweet et le nombre d'images dans le Tweet, entre 1 et 4.
- `distance` : Le nombre de bits de différence entre l'empreinte de l'image de requête et celle de l'image trouvée.

Liste des status possibles (Dans l'ordre de traitement) :
- `WAIT_LINK_FINDER` : En attente de traitement par un thread de Link Finder.
- `LINK_FINDER` : En cours de traitement par un thread de Link Finder.
- `WAIT_INDEX_ACCOUNTS_TWEETS` : En attente de traitement par un thread de lancement de l'indexation ou de la mise à jour de l'indexation des Tweets des comptes Twitter de l'artiste.
- `INDEX_ACCOUNTS_TWEETS` : En cours de traitement par les threads d'indexation des Tweets des comptes Twitter de l'artiste.
  - Si le champs `has_first_time_scan` est à `false`, c'est seulement pour une mise à jour des comptes, car l'illustration est trop récente.
  - Sinon, c'est qu'il y a un ou plusieurs comptes qui étaient inconnus dans la base de données. Cette étape va donc être longue.
- `WAIT_IMAGE_REVERSE_SEARCH` : En attente de traitement par un thread de recherche d'image inversée.
- `IMAGE_REVERSE_SEARCH` : En cours de traitement par un thread de recherche d'image inversée.
- `END` : Fin de traitement.

Liste des erreurs possibles :
- `NO_URL_FIELD` : Il n'y a pas de paramètre / argument `url` dans l'URL de requête.
- `NOT_AN_URL` : L'entrée du paramètre / argument `url` n'est pas une URL.
- `UNSUPPORTED_WEBSITE` : Le site passé en paramètre n'est pas supporté, ou l'URL est invalide.
- `NOT_AN_ARTWORK_PAGE` : Le site est supporté, mais l'URL entrée ne mène pas à une illustration.
- `NO_TWITTER_ACCOUNT_FOUND` : Aucun compte Twitter trouvé pour l'artiste de l'illustration.
- `NO_VALID_TWITTER_ACCOUNT_FOUND` : Des comptes Twitter ont étés trouvés, mais ils sont invalides.
- `BLOCKED_BY_TWITTER_ACCOUNT` : Un des comptes Twitter à indexer bloque tous les comptes de scan du serveur. Il est donc impossible d'indexer ce compte.
- `ERROR_DURING_REVERSE_SEARCH` : Erreur durant la recherche d'image inversée. Est ce que l'illustration n'a pas un format à la noix ? Par exemple GIF animé ?
- `QUERY_IMAGE_TOO_BIG` : L'illustration de requête est trop grande pour être traitée.
- `PROCESSING_ERROR` : Un thread de traitement a planté durant son traitement de cette requête. Il est donc impossible de terminer cette requête !
- `YOUR_IP_HAS_MAX_PROCESSING_REQUESTS` : L'adresse IP qui a envoyé la requête a atteint son quota maximum de requêtes en cours de traitement. Il faut donc attendre que les autres requêtes envoyées par cette adresse IP finissend leur traitement. 

La liste `results` peut être vide, ou comporter plusieurs résultats. Ils sont alors classés par ordre croissant de distance avec l'illustration de requête.

L'API peut aussi fournir des statistiques sur la base de données : `GET /stats`

Attention : Le serveur limite :
- Le nombre de requêtes en cours de traitement par adresse IP. Si dépassement, le JSON de réponse contient l'erreur : `YOUR_IP_HAS_MAX_PROCESSING_REQUESTS`.
- Et le nombre de requêtes par secondes. Si dépassement, le serveur renvoit une erreur HTTP 429.
