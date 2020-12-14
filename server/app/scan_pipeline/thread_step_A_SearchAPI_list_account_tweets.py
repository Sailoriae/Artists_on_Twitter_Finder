#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from tweet_finder import Tweets_Lister_with_SearchAPI, Unfounded_Account_on_Lister_with_SearchAPI, Blocked_by_User_with_SearchAPI


"""
ETAPE A du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread de listage des Tweets d'un compte Twitter en utilisant l'API de recherche
de Twitter.
"""
def thread_step_A_SearchAPI_list_account_tweets( thread_id : int, shared_memory ) :
     # Initialisation du listeur de Tweets
    searchAPI_lister = Tweets_Lister_with_SearchAPI( param.API_KEY,
                                                     param.API_SECRET,
                                                     param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN"],
                                                     param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN_SECRET"],
                                                     param.TWITTER_API_KEYS[ thread_id - 1 ]["AUTH_TOKEN"],
                                                     DEBUG = param.DEBUG,
                                                     ENABLE_METRICS = param.ENABLE_METRICS )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_threads_registry = shared_memory.threads_registry
    shared_memory_scan_requests = shared_memory.scan_requests
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_scan_requests_queues_sem = shared_memory_scan_requests.queues_sem
    shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_prior_queue = shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_prior_queue
    shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_queue = shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_queue
    
    
    # Dire qu'on ne fait rien
    shared_memory_threads_registry.set_request( f"thread_step_A_SearchAPI_list_account_tweets_number{thread_id}", None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_service_alive
        if not shared_memory_scan_requests_queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
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
                    shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_prior_queue.put( request )
                else :
                    shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_queue.put( request )
            
            # Lacher le sémaphore et arrêter là, on ne peut pas la traiter
            shared_memory_scan_requests_queues_sem.release()
            request.release_proxy()
            continue
        
        # Dire qu'on a commencé à traiter cette requête
        request.started_SearchAPI_listing = True
        
        # Lacher le sémaphore
        shared_memory_scan_requests_queues_sem.release()
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_A_SearchAPI_list_account_tweets_number{thread_id}", request )
        
        # On liste les tweets du compte Twitter de la requête avec l'API de recherche
        print( f"[step_A_th{thread_id}] Listage des Tweets du compte Twitter @{request.account_name} avec l'API de recherche." )
        request_SearchAPI_tweets_queue = request.SearchAPI_tweets_queue
        try :
            request.SearchAPI_last_tweet_date = searchAPI_lister.list_searchAPI_tweets( request.account_name,
                                                                                        request_SearchAPI_tweets_queue,
                                                                                        account_id = request.account_id,
                                                                                        add_step_A_time = shared_memory_execution_metrics.add_step_A_time )
        except Unfounded_Account_on_Lister_with_SearchAPI :
            request.unfounded_account = True
        
        except Blocked_by_User_with_SearchAPI :
            request.blocks_list += [ thread_id - 1 ] # Ne peut pas faire de append avec Pyro
            if request.is_prioritary :
                shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_prior_queue.put( request )
            else :
                shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_queue.put( request )
        
        request_SearchAPI_tweets_queue.release_proxy()
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_A_SearchAPI_list_account_tweets_number{thread_id}", None )
        
        # Forcer la fermeture du proxy
        request.release_proxy()
    
    print( f"[step_A_th{thread_id}] Arrêté !" )
    return
