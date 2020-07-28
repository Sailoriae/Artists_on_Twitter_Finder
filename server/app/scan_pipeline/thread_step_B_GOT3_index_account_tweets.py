#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from tweet_finder import CBIR_Engine_with_Database


"""
ETAPE B du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread d'indexation des tweets d'un compte Twitter, avec la librairie
GetOldTweets3.
"""
def thread_step_B_GOT3_index_account_tweets( thread_id : int, shared_memory ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database( DEBUG = param.DEBUG )
    
    # Dire qu'on ne fait rien
    shared_memory.scan_requests.requests_in_thread[ "thread_step_B_GOT3_index_account_tweets_number" + str(thread_id) ] = None
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_service_alive
        if not shared_memory.scan_requests.queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory.scan_requests.step_B_GOT3_index_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory.scan_requests.step_B_GOT3_index_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                shared_memory.scan_requests.queues_sem.release()
                sleep( 1 )
                continue
        
        # Lacher le sémaphore
        shared_memory.scan_requests.queues_sem.release()
        
        # Si la requête est annulée, on la jette
        if request.is_cancelled :
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread[ "thread_step_B_GOT3_index_account_tweets_number" + str(thread_id) ] = request
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        shared_memory.scan_requests.set_request_to_next_step( request )
        
        # On index / scan les comptes Twitter de la requête avec GetOldTweets3
        print( "[step_B_th" + str(thread_id) + "] Indexation / scan du compte Twitter @" + request.account_name + " avec GetOldTweets3." )
        cbir_engine.index_or_update_all_account_tweets( request.account_name, request.get_GOT3_list_result )
        
        # Vider la liste get_GOT3_list_result parce que c'est lourd et qu'on
        # en n'aura plus besoin
        request.get_GOT3_list_result = []
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread[ "thread_step_B_GOT3_index_account_tweets_number" + str(thread_id) ] = None
        
        # On passe la requête à l'étape suivante
        # C'est la procédure shared_memory.scan_requests.set_request_to_next_step
        # qui vérifie si elle peut
        shared_memory.scan_requests.set_request_to_next_step( request )
    
    print( "[step_B_th" + str(thread_id) + "] Arrêté !" )
    return
