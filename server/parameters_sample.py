#!/usr/bin/python3
# coding: utf-8

"""
Activer le mode multi-processus.

Si ce paramètre activé, de nombreux sous-processus seront créés, ainsi qu'un
serveur de mémoire partagée reposant sur la librairie PYRO sera créé. Le
serveur sera donc plus lourd, mais le traitement des requêtes sera bien plus
efficace.

Si ce paramètre est désactivé, seulement des threads seront créés, et la
mémoire partagée sera simplement un objet Python. Le serveur sera donc plus
léger, mais le traitement des requêtes sera plus lent, car les threads Python
ne fonctionnent pas en paralléle (Voir la doc sur le GIL). 

ATTENTION ! SQLite bloque la BDD lors d'une écriture ! Ne pas activer ce
paramètre si vous utilisez SQLite !
"""
ENABLE_MULTIPROCESSING = True

"""
Paramètres pour l'accès à l'API Twitter.
https://developer.twitter.com/en/apps
Il est très recommandé de paramètrer l'app Twitter pour qu'elle un un accès en
lecture seule.

Pour obtenir OAUTH_TOKEN et OAUTH_TOKEN_SECRET, vous pouvez utiliser le script
"get_oauth_token.py" présent dans le répertoire "misc".
"""
API_KEY = ""
API_SECRET = ""

OAUTH_TOKEN = ""
OAUTH_TOKEN_SECRET = ""

"""
OAUTH_TOKEN et OAUTH_TOKEN_SECRET :
Liste de paramètres pour l'accès à l'API Twitter, idem à ci-dessus, mais en
plusieurs exemplaires (Donc sur plusieurs comptes) pour paralléliser les
listages de Tweets

AUTH_TOKEN : Token de connexion à des comptes Twitter.
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

LES AUTH_TOKEN DOIVENT CORRESPONDRE AUX COUPLES OAUTH_TOKEN / OAUTH_TOKEN_SECRET !
C'est super méga important !
"""
TWITTER_API_KEYS = [ {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : "",
                       "AUTH_TOKEN" : ""
                      }, {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : "",
                       "AUTH_TOKEN" : ""
                      }, {
                       "OAUTH_TOKEN" : "",
                       "OAUTH_TOKEN_SECRET" : "",
                       "AUTH_TOKEN" : ""
                      } ]

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

Note : Le nombre de threads de listages (Etapes A et C) dépendent du nombre de
tokens de connexion à l'API Twitter que vous passez. Voir la liste
"TWITTER_API_KEYS".
Plus exactement, il y a un thread de listage avec l'API de recherche (Etape A)
par clé "AUTH_TOKEN", et un thread de listage avec l'API de timeline (Etape B)
par couples de clés "OAUTH_TOKEN" et "OAUTH_TOKEN_SECRET".
"""
NUMBER_OF_STEP_1_LINK_FINDER_THREADS = 5
NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS = 5
NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS = 5
NUMBER_OF_STEP_C_INDEX_ACCOUNT_TWEETS = len( TWITTER_API_KEYS ) * 2

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
Entête HTTP "User-Agent" qui est utilisé pour :
- Scrapper les sites supportés (Etape 1 : Link Finder),
- Obtenir les images des Tweets à indexer (Etape C : Indexation),
- Obtenir l'image de requête (Etape 3 : Recherche inversée).

Mettre ici un vrai navigateur, sinon Pixiv renverra une erreur HTTP !
On prend Firefox ESR comme valeur par défaut.
"""
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"

"""
MàJ automatique des comptes dans la BDD.
Nombre de jours sans scan du compte Twitter pour le mettre à jour
automatiquement.

Attention : Afin de répartir les mises à jour dans le temps, le système de mise
à jour automatique peut prendre de l'avance et lancer la mise à jour d'un
compte avant ce nombre de jours ne se soit écoulé.
"""
DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE = 30 # jours

"""
Période en jours pour réset les curseurs d'indexation avec l'API de recherche.
En effet : Le moteur de recherche de Twitter fluctue, et est assez mal
documenté. Certains Tweets peuvent être désindexés ou réindexés.
Il est donc intéressant de temps en temps de réintialiser le curseur
d'indexation avec l'API de recherche pour chaque compte.
Cela ne supprime ou ne réindexe aucun Tweet dans la base ! On en ajoute juste.
La vitesse dépend donc essentiellement du thread de listage.

Attention : Comme pour la mise à jour automatique, le système de reset des
curseurs peut lancer une indexation en avance, afin de les répartir dans le
temps.
"""
RESET_SEARCHAPI_CURSORS_PERIOD = 365 # jours

"""
Limitation du nombre de requêtes (Via l'API HTTP) par addresse IP.
"""
MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS = 10

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
