# Artists on Twitter Finder : Scripts divers

## Script `get_oauth_token.py`

Permet d'obtenir les clés d'authentification à un compte Twitter.


## Script `test_getoldtweets3_rate_limits.py`

Permet de déterminer si GetOldTweets3 est limité par adresse IP ou par cookie `auth_token`.


## Script `test_tweepy_rate_limits.py`

Permet de déterminer si Tweepy (Et donc l'API publique de Twitter) est limité par adresse IP ou par clés d'authentification.


## Script `add_images_names.py`

Script inutile aujourd'hui, mais qui m'a permis d'ajouter les noms des images des Tweets déjà stockés dans ma base de données.

Sauvegardé dans ce GIT car son utilisation de la méthode `statuses_lookup()` de la librairie Tweepy est intéressante.
