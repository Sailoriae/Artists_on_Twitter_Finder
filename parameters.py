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
NUMBER_OF_LINK_FINDER_THREADS = 1
NUMBER_OF_LIST_ACCOUNT_TWEETS_THREADS = 1
NUMBER_OF_INDEX_TWITTER_ACCOUNT_THREADS = 1
NUMBER_OF_REVERSE_SEARCH_THREADS = 1
NUMBER_OF_HTTP_SERVER_THREADS = 1
