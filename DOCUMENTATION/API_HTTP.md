# Utilisation de l'API

Le serveur est utilisable via un serveur HTTP, depuis le même serveur, ou l'extérieur, en faisant un proxy sur Apache ou Nginx. Ne pas ouvrir le port du serveur !

Les requêtes sont indentifiées par leur URL. La méthode pour lancer une procédure ou obtenir le résultat est la même : `GET /url=[URL de l'illustration de requête]`

Par exemple : `GET /?url=https://www.deviantart.com/serafleur/art/Sailor-Moon-604185347`

Le serveur répond par un JSON qui contient toujours les mêmes champs :
```
{
	"status" : "END",
	"twitter_accounts" : [
		"serafleur"
	],
	"results" : [
		{ "tweet_id" : 797039787534262272, "distance" : 0.4124855017771303 }
	],
	"error" : ""
}
```

Liste des status possibles (Dans l'ordre de traitement) :
- `WAIT_LINK_FINDER` : En attente de traitement par un thread de Link Finder.
- `LINK_FINDER` : En cours de traitement par un thread de Link Finder.
- `WAIT_LIST_ACCOUNT_TWEETS` : En attente de traitement par un thread de listage des tweets d'un compte Twitter.
- `LIST_ACCOUNT_TWEETS`: En cours de traitement par un thread de listage des tweets d'un compte Twitter (Par la librairie GetOldTweets3).
- `WAIT_INDEX_ACCOUNT_TWEETS` : En attente de traitement par un thread d'indexation des tweets d'un compte Twitter.
- `INDEX_ACCOUNT_TWEETS` : En cours de traitement par un thread d'indexation des tweets d'un compte Twitter.
- `WAIT_IMAGE_REVERSE_SEARCH` : En attente de traitement par un thread de recherche d'image inversée.
- `IMAGE_REVERSE_SEARCH` : En cours de traitement par un thread de recherche d'image inversée.
- `END` : Fin de traitement.

Liste des erreurs possibles :
- `NO_URL_FIELD` : Il n'y a pas de paramètre / argument `url` dans l'URL de requête.
- `INVALID_URL` : L'URL passée en paramètre est invalide.
- `UNSUPPORTED_WEBSITE` : Le site passé en paramètre n'est pas supporté.
- `NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST` : Aucun compte Twitter trouvé pour l'artiste de l'illustration.
- `ERROR_DURING_REVERSE_SEARCH` : Erreur durant la recherche d'image inversée. Est ce que l'illustration n'a pas un format à la noix ? Par exemple GIF animé ?

La liste `results` peut être vide, ou comporter plusieurs résultats. Ils sont alors classés par ordre croissant de distance avec l'illustration de requête.

L'API peut aussi fournir des statistiques sur la base de données : `GET /stats`
