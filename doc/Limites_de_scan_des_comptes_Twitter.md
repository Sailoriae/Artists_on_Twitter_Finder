# Limites lors des scan des comptes Twitter

## Comment récupérer les Tweets d'un compte Twitter ?

Pour récupérer les Tweets d'un compte Twitter, il y a 5 moyens :

1. Utiliser la mèthode de l'API publique Twitter `GET statuses/user_timeline` pour récupérer les Tweets d'un compte.
   * Avantages :
     - Très simple d'utilisation,
     - Et on est certain de récupèrer tous les Tweets.
   * Inconvénients :
     - On ne peut pas demander à l'API de nous renvoyer que les Tweets avec médias,
     - On est limité au 3 200 Tweets les plus récents du compte, Retweets compris,
     - On est limité à 100 000 requêtes par jours sur cette mèthode (Mais comme les Tweets sont donnés par paquets de 100, cela signifie qu'on peut scanner 3 125 comptes par jours avec 3 200 Tweets par compte),
   * Documentation : https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline

2. Faire tourner les JavaScripts de l'UI web Twitter avec Selenium et chercher dans le HTML les Tweets avec BeautifulSoup.
   * Inconvénients :
     - Très compliqué à mettre en oeuvre,
     - Très lent,
     - Quand même limité à 3 200 Tweets par compte.

En cherchant sur GitHub des scripts Python pour faire ce travail, je n'ai trouvé que ces solutions. Et personne n'a cherché à reverse-engineer l'API des JavaScript de l'UI Twitter... Surement parce que c'est trop compliqué, et bien évidemment pas du tout documenté. En même temps, Twitter veulent qu'on paye, voir le moyen numéro 5.

3. Utiliser l'API de recherche standard ("Standard Search API") de l'API publique de Twitter.
   * Inconvénients :
     - On ne peut pas aller au delà de 7 jours dans le passé, c'est pour ça que GetOldTweets3 existe,
     - Certains comptes sont mal indexés, voir pas du tout indexés.
   * Documentation : https://developer.twitter.com/en/docs/tweets/search/overview/standard

4. Utiliser l'API de recherche utilisée par l'UI web : https://twitter.com/search
   Par exemple avec la librairie GetOldTweets3 (Mais qui ne fonctionne plus aujourd'hui) ou la librairie SNScrape.
   * Avantages :
     - Peut trouver tous les Teets d'un compte, aussi loin dans le passé que possible,
     - Peut filtrer les Retweets et les Tweets sans médias.
   * Inconvénients :
     - Certains comptes sont mal indexés, voir pas du tout indexés,
     - On ne peut pas voir les Tweets d'un compte marqué "sensible".
   * Github GetOldTweets3 : https://github.com/Mottl/GetOldTweets3
   * Github SNScrape : https://github.com/JustAnotherArchivist/snscrape

5. Payer une API de recherche illimité ("Full-archive") dans le temps, Premium ("Search Tweets: Full-archive endpoint") ou Entreprise ("Full-archive Search API"), de l'API publique de Twitter.
   * Avantages :
     - Peut trouver tous les Teets d'un compte, aussi loin dans le passé que possible,
     - Peut filtrer les Retweets et les Tweets sans médias.
   * Inconvénients :
     - La version gratuite est limité à 5 000 Tweets par mois (50 requêtes de 100 Tweets), la version payante la plus cher (1 899 USD/mois) à 1 250 000 (2 500 requêtes de 500 Tweets).
   * Comparaison entre les API de recherche de Twitter : https://developer.twitter.com/en/docs/tweets/search/overview
   * Prix des API "Full-archive" : https://developer.twitter.com/en/pricing/search-fullarchive
   * Attention : API à ne pas confondre avec sa version limité à 30 jours, Premium ("Search Tweets: 30-day endpoint") ou Entreprise ("Full-archive Search API").


## Moyens retenues pour Artists on Twitter Finder

Deux moyens on étés retenus, et fonctionnent indépendamment sur le serveur :
* La mèthode de l'API publique Twitter `GET statuses/user_timeline`,
* Et les API de recherche de l'UI web. On utilisait avant GetOldTweets3 (Mais l'API qu'il utilisait a été supprimée), et on utilise actuellement SNScrape.

Leur implémentation est complètement indépendante, ce qui permet d'être certain de récupérer le maximum de Tweets avec médias possibles des comptes Twitter scannés.

Note : Avant d'analyser un Tweet, le système vérifie qu'il n'est pas déjà présent dans la base de données. Si c'est le cas, comme les Tweets ne sont pas modifiables, aucune analyse n'est exécuté, et le système pass au Tweet suivant.


## Limites de scan des comptes Twitter

En modifiant un peu GetOldTweets3 ou aujourd'hui SNScrape, on lui passe un token d'authentification (`auth_token`), permettant de se montrer comme connecté avec un compte à l'API de Twitter, et non comme invité.
Ainsi, on peut récupérer les Tweets marqués sensibles, et les Tweets des comptes marqués sensibles. C'est pour cela qu'il est précisé dans le fichier `parameters.py` qui les `auth_token` doivent être ceux de comptes ayant le filtrage de la recherche désactivé.

Cependant, il y a toujours la limitation de l'indexation de Twitter : Certains comptes, notamment les comptes marqués sensibles, ou les comptes Tweetant beaucoup trop, sont mal indexés.

C'est pour cela qu'afin d'être le plus exhaustif possible, "Artists on Twitter Finder" utilise aussi l'API de timeline. Mais il est impossible de récupérer tous les Tweets de tous les comptes. Ainsi, les gros comptes, c'est à dire avec beaucoup de Tweets, peuvent être mal indexés.
