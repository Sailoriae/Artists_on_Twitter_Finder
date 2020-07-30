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

Ce compte doit pouvoir voir les illustrations sensibles !
Aller dans les Paramètres Pixiv, et mettre sur "Show" les champs "Explicit
content (R-18)" et "Ero-guro content (R-18G)".
Sinon, le serveur renvera l'erreur "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST" pour
ce genre d'illustrations.
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
USE_MYSQL_INSTEAD_OF_SQLITE = False
MYSQL_ADDRESS = "localhost"
MYSQL_PORT = 3306
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

Les valeurs NUMBER_OF_STEP_A_GOT3_LIST_ACCOUNT_TWEETS_THREADS et
NUMBER_OF_STEP_B_TWITTERAPI_LIST_ACCOUNT_TWEETS_THREADS doivent rester à 1
En effet, ces threads font beaucoup d'appels aux API Twitter, et donc peuvent
recevoir des erreurs HTTP 429 "Too Many Requests".
Les créer une seule fois permet de limiter les erreur 429.
"""
NUMBER_OF_STEP_1_LINK_FINDER_THREADS = 5
NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS = 5
NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS = 5
NUMBER_OF_STEP_A_GOT3_LIST_ACCOUNT_TWEETS_THREADS = 1 # Laisser à 1
NUMBER_OF_STEP_B_TWITTERAPI_LIST_ACCOUNT_TWEETS_THREADS = 1 # Laisser à 1
NUMBER_OF_STEP_C_GOT3_INDEX_ACCOUNT_TWEETS = 5
NUMBER_OF_STEP_D_TWITTERAPI_INDEX_ACCOUNT_TWEETS = 5

"""
Faire plus de print().
"""
DEBUG = False

"""
MàJ automatique des comptes dans la BDD.
Nombre de jours sans scan du compte Twitter pour le mettre à jour
automatiquement.
"""
DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE = 10

"""
Limitation du nombre de requêtes (Via l'API HTTP) par addresse IP.
"""
MAX_PENDING_REQUESTS_PER_IP_ADDRESS = 10

"""
Liste des addresses IP non-soumises à la limitation.
"""
UNLIMITED_IP_ADDRESSES = [ "127.0.0.1" ]
