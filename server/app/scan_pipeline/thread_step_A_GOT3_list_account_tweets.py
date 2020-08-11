#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from tweet_finder import Tweets_Lister_with_GetOldTweets3, Unfounded_Account_on_Lister_with_GetOldTweets3


"""
ETAPE A du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread de listage des Tweets avec médias d'un compte Twitter, avec la librairie
GetOldTweets3.
"""
def thread_step_A_GOT3_list_account_tweets( thread_id : int, shared_memory ) :
     # Initialisation du listeur de Tweets
    getoldtweets3_lister = Tweets_Lister_with_GetOldTweets3( param.TWITTER_AUTH_TOKENS[ thread_id - 1 ],
                                                             DEBUG = param.DEBUG,
                                                             ENABLE_METRICS = param.ENABLE_METRICS )
    
    # Dire qu'on ne fait rien
    shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_A_GOT3_list_account_tweets_number" + str(thread_id), None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_service_alive
        if not shared_memory.scan_requests.queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory.scan_requests.step_A_GOT3_list_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory.scan_requests.step_A_GOT3_list_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                shared_memory.scan_requests.queues_sem.release()
                sleep( 1 )
                continue
        
        # Dire qu'on a commencé à traiter cette requête
        request.started_GOT3_listing = True
        
        # Lacher le sémaphore
        shared_memory.scan_requests.queues_sem.release()
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_A_GOT3_list_account_tweets_number" + str(thread_id), request )
        
        # On liste les tweets du compte Twitter de la requête avec GetOldTweets3
        print( "[step_A_th" + str(thread_id) + "] Listage des Tweets du compte Twitter @" + request.account_name + " avec GetOldTweets3." )
        try :
            request.GetOldTweets3_last_tweet_date = getoldtweets3_lister.list_getoldtweets3_tweets( request.account_name,
                                                                                                    request.GetOldTweets3_tweets_queue_put,
                                                                                                    add_step_A_time = shared_memory.execution_metrics.add_step_A_time )
        except Unfounded_Account_on_Lister_with_GetOldTweets3 :
            request.unfounded_account = True
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_A_GOT3_list_account_tweets_number" + str(thread_id), None )
    
    print( "[step_A_th" + str(thread_id) + "] Arrêté !" )
    return
