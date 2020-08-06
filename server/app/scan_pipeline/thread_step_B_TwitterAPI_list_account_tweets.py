#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from tweet_finder import Tweets_Lister_with_TwitterAPI, Unfounded_Account_on_Lister_with_TwitterAPI


"""
ETAPE B du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread de listage des tweets d'un compte Twitter en utilisant l'API publique
de Twitter, via la librairie Tweepy.
"""
def thread_step_B_TwitterAPI_list_account_tweets( thread_id : int, shared_memory ) :
    # Initialisation du listeur de Tweets
    twitterapi_lister = Tweets_Lister_with_TwitterAPI( DEBUG = param.DEBUG, DISPLAY_STATS = param.DISPLAY_STATS )
    
    # Dire qu'on ne fait rien
    shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_B_TwitterAPI_list_account_tweets_number" + str(thread_id), None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_service_alive
        if not shared_memory.scan_requests.queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory.scan_requests.step_B_TwitterAPI_list_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory.scan_requests.step_B_TwitterAPI_list_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                shared_memory.scan_requests.queues_sem.release()
                sleep( 1 )
                continue
        
        # Dire qu'on a commencé à traiter cette requête
        request.started_TwitterAPI_listing = True
        
        # Lacher le sémaphore
        shared_memory.scan_requests.queues_sem.release()
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_B_TwitterAPI_list_account_tweets_number" + str(thread_id), request )
        
        # On liste les Tweets du compte Twitter de la requête avec l'API Twitter
        print( "[step_B_th" + str(thread_id) + "] Listage des Tweets du compte Twitter @" + request.account_name + " avec l'API Twitter." )
        try :
            request.TwitterAPI_last_tweet_id = twitterapi_lister.list_TwitterAPI_tweets( request.account_name,
                                                                                         request.TwitterAPI_tweets_queue,
                                                                                         add_step_B_time = shared_memory.execution_metrics.add_step_B_time )
        except Unfounded_Account_on_Lister_with_TwitterAPI :
            request.unfounded_account = True
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_B_TwitterAPI_list_account_tweets_number" + str(thread_id), None )
    
    print( "[step_B_th" + str(thread_id) + "] Arrêté !" )
    return
