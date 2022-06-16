#!/usr/bin/python3
# coding: utf-8

"""
Activer le mode multi-processus.

Si ce paramètre activé, de nombreux processus fils seront créés, ainsi qu'un
serveur de mémoire partagée reposant sur la librairie Pyro. Le serveur sera
donc plus lourd, mais le traitement des requêtes sera bien plus efficace.

Si ce paramètre est désactivé, seulement des threads seront créés, et la
mémoire partagée sera simplement un objet Python. Le serveur sera donc plus
léger, mais le traitement des requêtes sera plus lent, car les threads Python
ne fonctionnent pas en parallèle (Voir la doc sur le GIL).

ATTENTION ! SQLite bloque la BDD lors d'une écriture ! Ne pas activer ce
paramètre si vous utilisez SQLite !
"""
ENABLE_MULTIPROCESSING = True

"""
Couple de clés d'accès à l'API Twitter. Pour ovenir un couple de clés API_KEYS
et API_SECRET, il faut créer une "application" sur l'interface Twitter pour les
développeurs : https://developer.twitter.com/en/apps

Il est très recommandé de paramétrer cette app Twitter pour qu'elle un accès en
lecture seule.
"""
API_KEY = ""
API_SECRET = ""

"""
Couple de clés d'accès au compte Twitter par défaut.
Ce compte est utilisé par :
- L'interface en ligne de commande
- Le thread de mise à jour automatique
- Le thread de reset des curseurs d'indexation avec l'API de recherche
- Le thread de retentative d'indexation des Tweets (Uniquement si un ID de
  Tweet a été inséré manuellement dans la base de données)
- Certains threads de Link Finder (Etape 1)
- Certains threads de recherche par image (Etape 3)
- Le script de maintenance permettant de désindexer les comptes supprimés

Pour obtenir des couples de clés OAUTH_TOKEN et OAUTH_TOKEN_SECRET, vous pouvez
utiliser le script "get_oauth_token.py" présent dans le répertoire "misc". Il
faudra vous munir du couple de clé API_KEY et API_SECRET ci-dessus.
"""
OAUTH_TOKEN = ""
OAUTH_TOKEN_SECRET = ""

"""
Liste de couples de clés d'accès à des comptes Twitter.
Cela permet de paralléliser le traitement, et donc d'améliorer les performances
du serveur. Ces comptes sont utilisés pour :
- Les threads de Link Finder (Etape 1)
- Les threads de recherche par image (Etape 3)
- Les threads de listage avec l'API de recherche (Etape A)
- Les threads de listage avec l'API de timeline (Etape B)

Ces couples de clés sont associées à une troisième clé AUTH_TOKEN, permettant
l'accès aux mêmes compte Twitter, mais via l'API de recherche (Etape A). Pour
obtenir ces clés, vous devez :
1. Ouvrir un compte Twitter dans un navigateur,
2. Copier ici la valeur du cookie "auth_token",
3. Et ne surtout pas déconnecter ce compte, ni effacer la session !
   Effacer les cookies du navigateur plutôt.

LES AUTH_TOKEN DOIVENT CORRESPONDRE AUX COUPLES OAUTH_TOKEN/OAUTH_TOKEN_SECRET.
C'est super méga important ! Sinon la vérification du blocage par un compte
lors de son indexation avec l'API de recherche risque d'être faussée, et le
compte mal indexé.

Ces comptes utilisés doivent pouvoir voir les médias sensibles dans les
recherches ! Pour se faire, il faut :
- Cocher la case "Afficher les médias au contenu potentiellement sensible" dans
  "Paramètres" -> "Confidentialité et sécurité" -> "Contenu que vous voyez"
- Décocher la case "Masquer les contenus offensants" dans "Paramètres" ->
  "Confidentialité et sécurité" -> "Contenu que vous voyez" ->
  "Paramètres de recherche"

Il est très recommandé d'utiliser ici des comptes "inutiles", en cas de
piratage du serveur (Et de vol des "auth_token" ci-dessous).

Plus vous mettez de clés ici, plus le serveur aura de threads (Et de processus
fils si le mode multi-processus est activé). Il est inutile de mettre plus de
comptes que vous n'avez de cœurs dans votre processeur.
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
NE PAS OUVRIR AU PUBLIC ! Utiliser un vrai serveur web comme Apache 2 ou Nginx
pour faire un proxy vers le serveur AOTF.
"""
HTTP_SERVER_PORT = 3301

"""
Faire plus de print().
Active aussi des écritures dans le fichier "debug.log". Cela permet d'avoir des
informations de débug qu'on ne peut pas voir dans le terminal.
"""
DEBUG = False

"""
Activer la mesure des temps d'exécutions des procédures longues.
Les moyennes sont alors accessibles via la commande "metrics".
"""
ENABLE_METRICS = True

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
Période en jours pour reset les curseurs d'indexation avec l'API de recherche.
En effet : Le moteur de recherche de Twitter fluctue, et est assez mal
documenté. Certains Tweets peuvent être désindexés ou réindexés.
Il est donc intéressant de temps en temps de réinitialiser le curseur
d'indexation avec l'API de recherche pour chaque compte.
Cela ne supprime ou ne réindexe aucun Tweet dans la base ! On en ajoute juste.
La vitesse dépend donc essentiellement du thread de listage.

Attention : Comme pour la mise à jour automatique, le système de reset des
curseurs peut lancer une indexation en avance, afin de les répartir dans le
temps.
"""
RESET_SEARCHAPI_CURSORS_PERIOD = 365 # jours

"""
Limitation du nombre de requêtes (Via l'API HTTP) par adresse IP.
"""
MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS = 10

"""
Liste des adresses IP non-soumises à la limitation.
"""
UNLIMITED_IP_ADDRESSES = [ "127.0.0.1" ]

"""
Activer la journalisation des résultats.
Les résultats sont alors écrits dans le fichier "results.log". Chaque résultat
est au format JSON, un JSON par ligne car une ligne par résultat.
Le JSON est identique à celui renvoyé par l'API.
Attention ! Les résultats sont journalisés uniquement s’il n'y a pas eu de
problème ou d'erreur.
"""
ENABLE_LOGGING = False

"""
Ce fichier contient des clés d'accès à l'API de Twitter. Par mesure de
sécurité, on supprime son accès par n'importe qui. Cette ligne est
l'équivalent de la commande "chmod o-rwx".
Si vous le souhaitez, vous pouvez personnaliser ou supprimer ce
comportement.
"""
from os import chmod, lstat
from stat import S_IRWXO
chmod(__file__, lstat(__file__).st_mode & ~S_IRWXO)
