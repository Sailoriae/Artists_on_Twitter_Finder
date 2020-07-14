# Le problème des Tweets sensibles

Sur Twitter, certains comptes, et certains Tweets contenant des médias, sont marqués comme "sensibles". Ce sont par exemple des Tweets contenant des images érotiques, ou des comptes qui en postent beaucoup.

L'API de recherche utilisée par GetOldTweet ne retourne les Tweets marqués comme sensibles, et l'intégralité des Tweets des comptes marqués sensibles.

J'ai donc fais les deux améliorations suivantes :
- Modifier un peu la librairie GOT3 pour qu'on puisse s'y connecter avec un utilisateur Twitter (Via le Cookie `auth_token`),
- Et ajouter `(filter:safe OR -filter:safe)` à ma recherche.
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

4. Payer Twitter pour avoir accès aux API de recherche Premiums : La "Full-Archive API" (Et pas une "30-day Search API"), ou la "Premium Search API" (API de recherche avec autorisation d'aller plus loin que 7 jours, mais c'est limité à 30). Bref : Oui mais :
   - C'EST CHER !
   - ARGENT !
   - C'est une API de recherche, donc si l'utilisateur n'est pas indexé, ça ne sert à rien.

En cherchant sur GitHub des scripts Python pour faire ce travail, je n'ai trouvé que ces solutions. Personne n'a cherché à reverse-engineer l'API des JavaScript de l'UI Twitter... Surement parce que c'est trop compliqué, et bien évidemment pas du tout documenté. En même temps, ils veulent qu'on paye. :D

**Conclusion : GetOldTweets3, c'est bien, et tant pis pour les tweets sensibles.**

**PS :** GOT3 ne permet pas non plus de trouver les Tweets de comptes qui ne sont pas indexés dans le moteur de recherche. Mais ce sont souvent des robots qui sont dans ce cas, et non des artistes.

___

**NON EN FAIT !** Exemple : @MayoRiyo, avec se 17 000 médias (juillet 2020)... GOT3 n'en trouve que 171. Aie ! Parce que cet artiste est mal indexé dans la recherche !

**Solution à trouver :** Obtenir l'intégralité des tweets d'un utilisateur, et pas depuis une API de recherche (Car GOT3 utilise une API de recherche).

Et c'est impossible, parce qu'on est dans tous les cas limité à 3 200 tweets. Même depuis l'UI web.

https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline

La solution la moins limité est donc l'API payante de Twitter. Et sans payer, c'est GetOldTweets3.

___

La seule solution pour améliorer est donc de payer l'API de recherche... Puisqu'il est impossible de dépasser la limite de 3 200 Tweets sur un compte, aucun moyen de payer pour dépasser.

Maximum du gratuit : 50 requêtes de 100 Tweets par mois. Donc 5 000 Tweets par mois. Autant oublie

2 500 requêtes de 500 tweets par mois, soit 1 250 000 Tweets par mois : 1 900 dollars. On oublie direct.

https://developer.twitter.com/en/pricing/search-fullarchive

La meilleure solution est donc GetOldTweets3... Ou un autre service comme Google Images ou 

___

Voir la méthode `get_GOT3_list()` de la classe `CBIR_Engine_with_Database` pour
l'utilisation de la désactivation du filtre "safe" la plus optimisée.'
