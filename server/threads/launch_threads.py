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

from threads.threads_launchers import launch_thread, launch_identical_threads_in_container, launch_unique_threads_in_container

from threads.user_pipeline.thread_step_1_link_finder import thread_step_1_link_finder
from threads.user_pipeline.thread_step_2_tweets_indexer import thread_step_2_tweets_indexer
from threads.user_pipeline.thread_step_3_reverse_search import thread_step_3_reverse_search

from threads.scan_pipeline.thread_step_A_SearchAPI_list_account_tweets import thread_step_A_SearchAPI_list_account_tweets
from threads.scan_pipeline.thread_step_B_TimelineAPI_list_account_tweets import thread_step_B_TimelineAPI_list_account_tweets
from threads.scan_pipeline.thread_step_C_index_account_tweets import thread_step_C_index_account_tweets
from threads.scan_pipeline.thread_retry_failed_tweets import thread_retry_failed_tweets

from threads.http_server.thread_http_server import thread_http_server

from threads.maintenance.thread_auto_update_accounts import thread_auto_update_accounts
from threads.maintenance.thread_reset_SearchAPI_cursors import thread_reset_SearchAPI_cursors
from threads.maintenance.thread_remove_finished_requests import thread_remove_finished_requests


"""
Fonction permettant de lancer les threads du serveur AOTF.

@param shared_memory_uri URI de la mémoire partagée, ou objet de la mémoire
                         partagée si on n'est pas en mode multi-processus.
@return Liste des threads et/ou processus créés.
"""
def launch_threads ( shared_memory_uri ) :
    threads_or_process = [] # Liste contenant tous les threads ou processus
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_1_link_finder,
        param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS,
        False, # Ne nécessitent pas des processus séparés (Seront placés dans un processus conteneur sui on est en Multiprocessing)
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_2_tweets_indexer,
        param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS,
        False, # Ne nécessitent pas des processus séparés
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_3_reverse_search,
        param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS,
        True, # Nécessitent des processus séparés (Car il font de la recherche de vecteurs similaires)
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_A_SearchAPI_list_account_tweets,
        len( param.TWITTER_API_KEYS ), # Il doit y avoir autant de threads de listage que de clés d'API dans TWITTER_API_KEYS
        False, # Ne nécessitent pas des processus séparés
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_B_TimelineAPI_list_account_tweets,
        len( param.TWITTER_API_KEYS ), # Il doit y avoir autant de threads de listage que de clés d'API dans TWITTER_API_KEYS
        False, # Ne nécessitent pas des processus séparés
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_C_index_account_tweets,
        param.NUMBER_OF_STEP_C_INDEX_ACCOUNT_TWEETS,
        True, # Nécessitent des processus séparés (Car ils font de l'indexation, donc de l'analyse d'images)
        shared_memory_uri ) )
    
    
    # On ne crée qu'un seul thread (ou processus) du serveur HTTP
    # C'est lui qui va créer plusieurs threads grace à la classe :
    # http.server.ThreadingHTTPServer()
    threads_or_process.append( launch_thread(
        thread_http_server,
        1, True, # Nécessite un processus séparé
        shared_memory_uri ) )
    
    
    # Liste des procédures de maintenance
    # Elles ne nécessitent pas d'être dans des processus séparés
    # Et elles doivent être uniques
    maintenance_procedures = []
    maintenance_procedures.append( thread_auto_update_accounts ) # Mise à jour automatique
    maintenance_procedures.append( thread_reset_SearchAPI_cursors ) # Reset des curseurs d'indexation avec l'API de recherche
    maintenance_procedures.append( thread_remove_finished_requests ) # Délestage de la liste des requêtes
    maintenance_procedures.append( thread_retry_failed_tweets ) # Retentative d'indexation de Tweets
    
    # Lancer les procédures de maintenance
    threads_or_process.extend( launch_unique_threads_in_container(
        maintenance_procedures,
        False, # Ne nécessitent pas des processus séparés
        "thread_maintenance", # Respecte la convention de nommage
        shared_memory_uri ) )
    
    return threads_or_process
