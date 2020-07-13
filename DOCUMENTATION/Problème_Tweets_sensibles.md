# Le problème des Tweets sensibles

Sur Twitter, certains comptes, et certains Tweets contenant des médias, sont marqués comme "sensibles". Ce sont par exemple des Tweets contenant des images érotiques, ou des comptes qui en postent beaucoup.

L'API de recherche utilisée par GetOldTweet ne retourne les Tweets marqués comme sensibles, et l'intégralité des Tweets des comptes marqués sensibles.

J'ai donc fais les deux améliorations suivantes :
- Modifier un peu la librairie GOT3 pour qu'on puisse s'y connecter avec un utilisateur Twitter (Via le Cookie `auth_token`),
- Et ajouter `-filter:safe` à ma recherche.
Ces deux améliorations (Ensemble, l'une ou l'autre seule ne sert à rien) font que l'API peut retourner en plus les Tweets avec médias qui ne sont pas marqués sensibles des comptes marqués comme sensibles... Mais toujours pas les Tweets avec médias marqués sensibles !

Notre système est donc innefficace pour toute illustration que Twitter détecte comme sensible... Et des fois c'est juste des dunes de sable.

Bref. Il y aurait 4 alternatives à GOT3 :

1. Utiliser la vraie API publique Twitter de récupération des Tweets d'un compte... Oui mais :
   - On ne peut pas filtrer ni les retweets, ni les Tweets sans médias.
   - On est limité à 3 200 Tweets par compte.
   - On est limité à 100 000 requêtes par jours.
   - Source : https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline
   - Tout ceci est très nul.

2. Faire tourner les JavaScripts de l'UI web Twitter avec Selenium et chercher dans le HTML les Tweets avec BeautifulSoup... Oui mais :
   - On est limité QUAND MEME sur le nombre de Tweets par utilisateur, alors que c'est l'UI web.
   - C'est super lent !

3. Utiliser la vraie API publique Twitter de recherche... Oui mais :
   - On ne peut pas aller au delà de 7 jours dans le passé, c'est pour ça que GetOldTweets3 existe.

4. Payer Twitter pour avoir accès à la "Full-Archive API" (Et pas une "30-day Search API"), ou la "Premium Search API" (API de recherche avec autorisation d'aller plus loin que 7 jours, mais c'est limité à 30 si j'ai bien compris)... Et je n'ai pas bien compris la différence... Bref : Oui mais :
   - C'EST CHER !
   - ARGENT !

En cherchant sur GitHub des scripts Python pour faire ce travail, je n'ai trouvé que ces solutions. Personne n'a cherché à reverse-engineer l'API des JavaScript de l'UI Twitter... Surement parce que c'est trop compliqué, et bien évidemment pas du tout documenté. En même temps, ils veulent qu'on paye. :D

**Conclusion : GetOldTweets3, c'est bien, et tant pis pour les tweets sensibles.**

**PS :** GOT3 ne permet pas non plus de trouver les Tweets de comptes qui ne sont pas indexés dans le moteur de recherche. Mais ce sont souvent des robots qui sont dans ce cas, et non des artistes.
