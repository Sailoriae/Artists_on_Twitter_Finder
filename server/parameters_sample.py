#!/usr/bin/python3
# coding: utf-8

"""
Activer le multiprocessing. Prend alors plus de processeur, mais le traitement
des requêtes est plus efficace.
ATTENTION ! SQLite bloque la BDD lors d'une écriture ! Ne pas activer ce
paramètre si vous utilisez SQLite !
"""
ENABLE_MULTIPROCESSING = True

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
Liste de paramètres pour l'accès à l'API Twitter, idem à ci-dessus, mais en
plusieurs exemplaires (Donc sur plusieurs comptes) pour paralléliser les
listages de Tweets
"""
TWITTER_API_KEYS = [ {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : ""
                      }, {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : ""
                      }, {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : ""
                      } ]

"""
Token de connexion à des comptes Twitter.
1. Ouvrir un compte Twitter dans un navigateur,
2. Mettre ici la valeur du cookie "auth_token",
3. Et ne surtout pas déconnecter ce compte, ni effacer la session !
   Effacer les cookies du navigateur plutôt.

Ces comptes utilisés doivent pouvoir voir les médias sensibles dans les
recherches ! OPTION A DECOCHER :
Paramètres -> Confidentialité et sécurité -> Sécurité -> Filtres de recherche
-> Masquer les contenus offensants

Il est très recommandé d'utiliser ici des comptes "inutiles", en cas de
piratage du serveur (Et de vol des "auth_token" ci-dessous).
"""
TWITTER_AUTH_TOKENS = [ "",
                        "",
                        "" ]

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
"""
NUMBER_OF_STEP_1_LINK_FINDER_THREADS = 5
NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS = 5
NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS = 5
NUMBER_OF_STEP_4_FILTER_RESULTS_THREADS = 5
NUMBER_OF_STEP_A_SEARCHAPI_LIST_ACCOUNT_TWEETS_THREADS = len( TWITTER_AUTH_TOKENS ) # NE PAS TOUCHER
NUMBER_OF_STEP_B_TIMELINEAPI_LIST_ACCOUNT_TWEETS_THREADS = len( TWITTER_API_KEYS ) # NE PAS TOUCHER
NUMBER_OF_STEP_C_SEARCHAPI_INDEX_ACCOUNT_TWEETS = len( TWITTER_AUTH_TOKENS ) * 3
NUMBER_OF_STEP_D_TIMELINEAPI_INDEX_ACCOUNT_TWEETS = len( TWITTER_API_KEYS ) * 2

"""
Faire plus de print().
"""
DEBUG = False

"""
Activer la mesure des temps d'éxécutions des procédures longues.
Les moyennes sont alors accessibles via la commande "metrics".
"""
ENABLE_METRICS = True

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

"""
Activer la journalisation des résultats.
Les résultats sont alors écrits dans le fichier "results.log". Chaque résultat
est au format JSON, un JSON par ligne car une ligne par résultat.
Le JSON est identique à celui renvoyé par l'API.
Attention ! Les résultats sont journalisés uniquement si il n'y a pas eu de
problème ou d'erreur.
"""
ENABLE_LOGGING = False
