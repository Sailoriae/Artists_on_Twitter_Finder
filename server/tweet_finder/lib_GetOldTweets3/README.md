# GetOldTweets3

Ceci est une librairie Python indépendante du serveur "Artists on Twitter Finder".

Plus d'informations ici :
https://github.com/Mottl/GetOldTweets3

Cette libairie a été incluse ici car le serveur nécessite quelques modifications :
* Attente et ré-essai lors d'une erreur 429 ou 503,
* Détection des médias dans les Tweets scannés, et renvoie de leurs URLs,
* Et possibilité d'envoyer un Cookie `auth_token` à l'API Twitter.

Cette librairie est dans sa dernière version de sa branche `master` au 4 mai 2020, c'est à dire le commit suivant :
https://github.com/Mottl/GetOldTweets3/commit/54a8e73d56953c7f664e073e121fa1413de4fbff
```
Merge pull request #64 from MichaelKarpe/master
Adds minimum engagement and "none of these words" filters
```
