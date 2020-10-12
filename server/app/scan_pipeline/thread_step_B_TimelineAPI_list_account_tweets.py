#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from tweet_finder import Tweets_Lister_with_TimelineAPI, Unfounded_Account_on_Lister_with_TimelineAPI, Blocked_by_User_with_TimelineAPI


"""
ETAPE B du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread de listage des tweets d'un compte Twitter en utilisant l'API de timeline
de Twitter.
"""
def thread_step_B_TimelineAPI_list_account_tweets( thread_id : int, shared_memory ) :
    # Initialisation du listeur de Tweets
    timelineAPI_lister = Tweets_Lister_with_TimelineAPI( param.API_KEY,
                                                         param.API_SECRET,
                                                         param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN"],
                                                         param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN_SECRET"],
                                                         DEBUG = param.DEBUG,
                                                         ENABLE_METRICS = param.ENABLE_METRICS )
    
    # Dire qu'on ne fait rien
    shared_memory.threads_registry.set_request( "thread_step_B_TimelineAPI_list_account_tweets_number" + str(thread_id), None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_service_alive
        if not shared_memory.scan_requests.queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory.scan_requests.step_B_TimelineAPI_list_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory.scan_requests.step_B_TimelineAPI_list_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                shared_memory.scan_requests.queues_sem.release()
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
                    shared_memory.scan_requests.step_B_TimelineAPI_list_account_tweets_prior_queue.put( request )
                else :
                    shared_memory.scan_requests.step_B_TimelineAPI_list_account_tweets_queue.put( request )
            
            # Lacher le sémaphore et arrêter là, on ne peut pas la traiter
            shared_memory.scan_requests.queues_sem.release()
            continue
        
        # Dire qu'on a commencé à traiter cette requête
        request.started_TimelineAPI_listing = True
        
        # Lacher le sémaphore
        shared_memory.scan_requests.queues_sem.release()
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.threads_registry.set_request( "thread_step_B_TimelineAPI_list_account_tweets_number" + str(thread_id), request )
        
        # On liste les Tweets du compte Twitter de la requête avec l'API de timeline
        print( "[step_B_th" + str(thread_id) + "] Listage des Tweets du compte Twitter @" + request.account_name + " avec l'API de timeline." )
        try :
            request.TimelineAPI_last_tweet_id = timelineAPI_lister.list_TimelineAPI_tweets( request.account_name,
                                                                                            request.TimelineAPI_tweets_queue,
                                                                                            account_id = request.account_id,
                                                                                            add_step_B_time = shared_memory.execution_metrics.add_step_B_time )
        except Unfounded_Account_on_Lister_with_TimelineAPI :
            request.unfounded_account = True
        
        except Blocked_by_User_with_TimelineAPI :
            request.blocks_list += [ thread_id - 1 ] # Ne peut pas faire de append avec Pyro
            if request.is_prioritary :
                shared_memory.scan_requests.step_B_TimelineAPI_list_account_tweets_prior_queue.put( request )
            else :
                shared_memory.scan_requests.step_B_TimelineAPI_list_account_tweets_queue.put( request )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.threads_registry.set_request( "thread_step_B_TimelineAPI_list_account_tweets_number" + str(thread_id), None )
    
    print( "[step_B_th" + str(thread_id) + "] Arrêté !" )
    return
