#!/usr/bin/python3
# coding: utf-8

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    from os import getcwd as get_wdir
    from sys import path
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( ".." )
    path.append(get_wdir())

import parameters as param


"""
Paramétrage du nombre de threads.
"""
# Etape 1 : Autant de threads que de couples d'accès à l'API Twitter
# "+1" parce qu'il y a aussi le compte par défaut
NUMBER_OF_STEP_1_LINK_FINDER_THREADS = len( param.TWITTER_API_KEYS ) + 1

# Etape 2 : Autant de threads que de threads de Link Finder
NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS = NUMBER_OF_STEP_1_LINK_FINDER_THREADS

# Etape 3 : Autant de threads que de threads de Link Finder
NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS = NUMBER_OF_STEP_1_LINK_FINDER_THREADS

# Etape A : Autant de threads que clés d'accès à l'API Twitter de recherche
# On ne comprend par le compte par défaut, car il n'a pas de clé "auth_token"
NUMBER_OF_STEP_A_SEARCHAPI_LIST_ACCOUNT_TWEETS = len( param.TWITTER_API_KEYS ) # NE PAS MODIFIER

# Etape B : Autant de threads que de couples d'accès à l'API Twitter
# On ne comprend par le compte par défaut pour être égale au nombre de threads
# de listage avec l'API de recherche (Etape A)
NUMBER_OF_STEP_B_TIMELINEAPI_LIST_ACCOUNT_TWEETS = len( param.TWITTER_API_KEYS ) # NE PAS MODIFIER

# Etape C : Autant de threads d'indexation que de threads de listage
NUMBER_OF_STEP_C_INDEX_TWEETS = len( param.TWITTER_API_KEYS ) * 2

"""
Entête HTTP "User-Agent" qui est utilisé pour :
- Scrapper les sites supportés (Etape 1 : Link Finder),
- Obtenir les images des Tweets à indexer (Etape C : Indexation),
- Obtenir l'image de requête (Etape 3 : Recherche inversée).

Mettre ici un vrai navigateur, sinon Pixiv renverra une erreur HTTP !
On prend Firefox ESR comme valeur par défaut.
"""
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
