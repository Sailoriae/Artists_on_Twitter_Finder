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

4. Utiliser la librairie Python GetOldTweets3.
   * Avantages :
     - Peut trouver tous les Teets d'un compte, aussi loin dans le passé que possible,
     - Peut filtrer les Retweets et les Tweets sans médias.
   * Inconvénients :
     - Certains comptes sont mal indexés, voir pas du tout indexés,
     - On ne peut pas voir les Tweets d'un compte marqué "sensible".
   * Github : https://github.com/Mottl/GetOldTweets3

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

Deux moyens on étés retenus, et fonctionnent indépendemment sur le serveur :
* La mèthode de l'API publique Twitter `GET statuses/user_timeline`,
* Et la librairie Python GetOldTweets3.

Leur implémentation est complètement indépendante, ce qui permet d'être certain de récupérer le maximum de Tweets avec médias possibles des comptes Twitter scannés.

Note : Avant d'analyser un Tweet, le système vérifie qu'il n'est pas déjà présent dans la base de données. Si c'est le cas, comme les Tweets ne sont pas modifiables, aucune analyse n'est exécuté, et le système pass au Tweet suivant.


## Limites de scan des comptes Twitter

### Premier problème de GetOldTweets3 : Les tweets sensibles

Sur Twitter, certains comptes, et certains Tweets contenant des médias, sont marqués comme "sensibles". Ce sont par exemple des Tweets contenant des images érotiques, ou des comptes qui en postent beaucoup.
Il y a aussi des Tweets marqués "semi-sensibles" (Ce n'est pas exactement le cas, mais considérons la chose ainsi pour l'explication qui va suivre), comme par exemple les Tweets contenant des jurons.

L'API utilisée par GetOldTweet3 est une API de recherche, et ne retourne pas les Tweets marqués comme sensibles, ni l'intégralité des Tweets des comptes marqués sensibles.

Cependant, nous avons implémenté deux améliorations à la recherche par GetOldTweets3 :
* Modifier un peu la librairie GOT3 pour qu'on puisse s'y connecter avec un utilisateur Twitter (Via le Cookie `auth_token`), ce qui permet d'utiliser les deux améliorations qui vont suivre,
* Ajouter ` (filter:safe OR -filter:safe)` à la recherche, ce qui permet de récupérer les Tweets "semi-sensibles" de comptes non-marqués "sensibles",
* Faire une seconde recherche avec ` -filter:safe` si la première n'a rien donné, ce qui permet de récupérer les Tweets non-marqués "sensibles" d'un compte marqué "sensible".

Ces deux améliorations permettent d'utiliser pleinement l'API Twitter utilisée par GetOldTweets3.

Cependant, ce système a été testé sur un compte marqué "sensible", postant uniquement des Tweet avec médias marqués "sensibles" (@Lewdlestia), et il a récupéré 12 000 Tweets sur les 16 000 Tweetés par ce compte (juillet 2020), grace à la première recherche ! La différence du nombre de Tweets est expliquable par le faire que ce compte soit un robot et est donc mal indexé, car il poste beaucoup de Tweets.

Nous ne pouvons pas expliquer ce comportement, car Twitter laissent beaucoup d'ombre sur leur système d'indexation et le marquage des Tweets en "sensibles".

Voir la méthode `get_GOT3_list()` de la classe `CBIR_Engine_with_Database` pour l'utilisation de la désactivation du filtre "safe" la plus optimisée.

### Second problème de GetOldTweets3 : La mauvaise indexation

Certains comptes, notamment ceux postant beaucoup (Souvent des robots), sont mal indexés dans la recherche Twitter. Donc, comme GetOldTweet3 utilise une API de recherche, l'historique des Tweets de ces comptes seront forcément incomplets.

Par exemple : Le compte @MayoRiyo a 17 000 Tweets avec médias (juillet 2020), et aucun problème de Tweets "sensibles", mais GetOldTweets3 n'en trouve que 171... Aie ! Parce que cet artiste est mal indexé dans la recherche !

### Solution : Rescanner le compte avec la mèthode de l'API publique Twitter `GET statuses/user_timeline`

Une deuxième passe (En vérité une troisième puisque GOT3 fait deux recherches) de scan est faite (Dans un thread séparé) via la librairie Tweepy sur la mèthode de l'API publique Twitter `GET statuses/user_timeline`.

Cette passe permet d'être certain des 3 200 Tweets les plus récents d'un compte. Dans le cas de @MayoRiyo, avec 90 000 Tweets (juillet 2020), cette passe ne sert pas à grand chose.

D'où la nécéssité de mettre souvent à jour les comptes dans la base de données ! C'est pour cela qu'il y a un tread qui lance une mise à jour automatique des comptes qui n'ont pas étés scannés depuis plus de 10 jours (Paramètre modifiable dans `parameters.py`, mais 10 jours est la valeur recommandée).
