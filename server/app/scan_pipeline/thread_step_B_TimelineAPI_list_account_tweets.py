#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    from os import getcwd as get_wdir
    from sys import path
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( "../.." )
    path.append(get_wdir())

import parameters as param
from tweet_finder.class_Tweets_Lister_with_TimelineAPI import Tweets_Lister_with_TimelineAPI
from tweet_finder.class_Tweets_Lister_with_TimelineAPI import Unfound_Account_on_Lister_with_TimelineAPI
from tweet_finder.class_Tweets_Lister_with_TimelineAPI import Blocked_by_User_with_TimelineAPI


"""
ETAPE B du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread de listage des tweets d'un compte Twitter en utilisant l'API de timeline
de Twitter.
"""
def thread_step_B_TimelineAPI_list_account_tweets( thread_id : int, shared_memory ) :
    # Vérifier qu'on a un bon numéro de thread
    if len( param.TWITTER_API_KEYS ) < thread_id :
        raise RuntimeError( "Il doit y avoir autant de threads de listage que de clés d'API dans \"TWITTER_API_KEYS\"." )
    
    # Initialisation du listeur de Tweets
    timelineAPI_lister = Tweets_Lister_with_TimelineAPI( param.API_KEY,
                                                         param.API_SECRET,
                                                         param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN"],
                                                         param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN_SECRET"],
                                                         DEBUG = param.DEBUG,
                                                         ENABLE_METRICS = param.ENABLE_METRICS )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_threads_registry = shared_memory.threads_registry
    shared_memory_scan_requests = shared_memory.scan_requests
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_scan_requests_queues_sem = shared_memory_scan_requests.queues_sem
    shared_memory_scan_requests_step_B_TimelineAPI_list_account_tweets_prior_queue = shared_memory_scan_requests.step_B_TimelineAPI_list_account_tweets_prior_queue
    shared_memory_scan_requests_step_B_TimelineAPI_list_account_tweets_queue = shared_memory_scan_requests.step_B_TimelineAPI_list_account_tweets_queue
    shared_memory_scan_requests_step_C_index_account_tweets_queue = shared_memory_scan_requests.step_C_index_account_tweets_queue
    
    # Dire qu'on ne fait rien
    shared_memory_threads_registry.set_request( f"thread_step_B_TimelineAPI_list_account_tweets_th{thread_id}", None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_service_alive
        if not shared_memory_scan_requests_queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory_scan_requests_step_B_TimelineAPI_list_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            request = None
        if request == None :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory_scan_requests_step_B_TimelineAPI_list_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                request = None
            if request == None :
                shared_memory_scan_requests_queues_sem.release()
                sleep( 1 )
                continue
        
        # Vérifier qu'on n'est pas bloqué par ce compte
        if thread_id - 1 in request.blocks_list :
            # Si tous les comptes qu'on a pour lister sont bloqués, on met la
            # requête en échec
            if len( request.blocks_list ) >= len( param.TWITTER_API_KEYS ) :
                request.has_failed = True
            
            # Sinon, on la remet dans la file
            else :
                if request.is_prioritary :
                    shared_memory_scan_requests_step_B_TimelineAPI_list_account_tweets_prior_queue.put( request )
                else :
                    shared_memory_scan_requests_step_B_TimelineAPI_list_account_tweets_queue.put( request )
            
            # Lacher le sémaphore et arrêter là, on ne peut pas la traiter
            shared_memory_scan_requests_queues_sem.release()
            request.release_proxy()
            continue
        
        # Dire qu'on a commencé à traiter cette requête
        # AVANT de lacher le sémaphore !
        request.started_TimelineAPI_listing = True
        
        # Lacher le sémaphore
        shared_memory_scan_requests_queues_sem.release()
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_B_TimelineAPI_list_account_tweets_th{thread_id}", request )
        
        # On liste les Tweets du compte Twitter de la requête avec l'API de timeline
        print( f"[step_B_th{thread_id}] Listage des Tweets du compte Twitter @{request.account_name} avec l'API de timeline." )
        try :
            timelineAPI_lister.list_TimelineAPI_tweets( request.account_name,
                                                        shared_memory_scan_requests_step_C_index_account_tweets_queue,
                                                        account_id = request.account_id,
                                                        add_step_B_time = shared_memory_execution_metrics.add_step_B_time,
                                                        request_uri = request.get_URI() )
        except Unfound_Account_on_Lister_with_TimelineAPI :
            request.unfound_account = True
        
        except Blocked_by_User_with_TimelineAPI :
            request.blocks_list += [ thread_id - 1 ] # Ne peut pas faire de append avec Pyro
            if request.is_prioritary :
                shared_memory_scan_requests_step_B_TimelineAPI_list_account_tweets_prior_queue.put( request )
            else :
                shared_memory_scan_requests_step_B_TimelineAPI_list_account_tweets_queue.put( request )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_B_TimelineAPI_list_account_tweets_th{thread_id}", None )
        
        # Forcer la fermeture du proxy
        request.release_proxy()
    
    print( f"[step_B_th{thread_id}] Arrêté !" )
    return
