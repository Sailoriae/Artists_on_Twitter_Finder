#!/usr/bin/python3
# coding: utf-8

"""
Paramètres pour l'accès à l'API Twitter.
https://developer.twitter.com/en/apps
Il est très recommandé de paramètrer l'app Twitter pour qu'elle un un accès en
lecture seule.
"""
API_KEY = ""
API_SECRET = ""

OAUTH_TOKEN = ""
OAUTH_TOKEN_SECRET = ""

"""
Token de connexion à un compte Twitter.
1. Ouvrir un compte Twitter dans un navigateur,
2. Mettre ici la valeur du cookie "auth_token",
3. Et ne surtout pas déconnecter ce compte, ni effacer la session !
   Effacer les cookies du navigateur plutôt.

Ce compte utilisé doit pouvoir voir les médias sensibles dans les recherches !
OPTION A DECOCHER :
Paramètres -> Confidentialité et sécurité -> Sécurité -> Filtres de recherche
-> Masquer les contenus offensants

Il est très recommandé d'utiliser ici un compte "inutile", en cas de piratage
du serveur (Et de vol de l'"auth_token" ci-dessous).
"""
TWITTER_AUTH_TOKEN = ""

"""
Paramètres pour l'accès à l'API Pixiv.
Il est très recommandé de ne pas utiliser un compte personnel !
"""
PIXIV_USERNAME = ""
PIXIV_PASSWORD = ""

"""
Paramètres pour l'utilisation de SQLite.
"""
SQLITE_DATABASE_NAME = "SQLite_Database.db"

"""
Paramètres pour l'utilisation de MySQL.
"""
MYSQL_ADDRESS = "localhost"
MYSQL_PORT = "3306"
MYSQL_USERNAME = ""
MYSQL_PASSWORD = ""
MYSQL_DATABASE_NAME = ""

"""
Port du serveur HTTP.
NE PAS OUVRIR AU PUBLIQUE ! Utiliser un vrai serveur web comme Apache 2 ou
Nginx comme proxy.
"""
HTTP_SERVER_PORT = 3301

"""
Paramètrage du nombre de threads.
"""
NUMBER_OF_STEP_1_LINK_FINDER_THREADS = 1
NUMBER_OF_STEP_2_GOT3_LIST_ACCOUNT_TWEETS_THREADS = 1
NUMBER_OF_STEP_3_GOT3_INDEX_ACCOUNT_TWEETS = 1
NUMBER_OF_STEP_4_TWITTERAPI_INDEX_ACCOUNT_TWEETS = 1
NUMBER_OF_STEP_5_REVERSE_SEARCH_THREADS = 1
NUMBER_OF_HTTP_SERVER_THREADS = 1

"""
Faire plus de print().
"""
DEBUG = False
