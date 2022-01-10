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
Fonction permettant d'augmenter le nombre maximum de descripteurs de fichiers.
En effet, chaque connexion au serveur de mémoire partagée (Proxy) est un
nouveau descripteur. Il en faut donc plus que la limite par défaut de 1024.

@return Le nombre de descripteurs de fichiers qu'on a défini.
"""
def define_max_file_descriptors () :
    # Threads de traitement (Etapes 1, 2, 3, A, B et C)
    max_fd = 0
    max_fd += 300 * param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS
    max_fd += 300 * param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS
    max_fd += 300 * param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS
    max_fd += 300 * len( param.TWITTER_API_KEYS ) # Nombre de threads de listage avec l'API de recherche (Etape A)
    max_fd += 300 * len( param.TWITTER_API_KEYS ) # Nombre de threads de listage avec l'API de timeline (Etape B)
    max_fd += 300 * param.NUMBER_OF_STEP_C_INDEX_ACCOUNT_TWEETS
    
    # Serveur HTTP et autres, même si on a déjà une bonne marge
    max_fd += 2000
    
    try :
        import resource
    except ModuleNotFoundError : # On n'est pas sous un système UNIX
        pass
    else :
        resource.setrlimit( resource.RLIMIT_NOFILE, (max_fd, max_fd) )
        print( f"Nombre maximum de descripteurs de fichiers : {max_fd}" )
    
    return max_fd
