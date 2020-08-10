#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep, time
from datetime import datetime

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from tweet_finder import Tweets_Indexer_with_TwitterAPI
from tweet_finder.database import SQLite_or_MySQL


"""
ETAPE D du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread d'indexation des tweets d'un compte Twitter trouvés par le listage avec
GetOldTweets3.
"""
def thread_step_D_TwitterAPI_index_account_tweets( thread_id : int, shared_memory ) :
    # Initialisation de l'indexeur de Tweets
    twitterapi_indexer = Tweets_Indexer_with_TwitterAPI( DEBUG = param.DEBUG, ENABLE_METRICS = param.ENABLE_METRICS )
    
    # Accès direct à la base de données
    # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
    bdd_direct_access = SQLite_or_MySQL()
    
    # Dire qu'on ne fait rien
    shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_D_TwitterAPI_index_account_tweets_number" + str(thread_id), None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_service_alive
        if not shared_memory.scan_requests.queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory.scan_requests.step_D_TwitterAPI_index_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory.scan_requests.step_D_TwitterAPI_index_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                shared_memory.scan_requests.queues_sem.release()
                sleep( 1 )
                continue
        
        # Lacher le sémaphore
        shared_memory.scan_requests.queues_sem.release()
        
        # Si le compte est marqué comme introuvable par un des thread de
        # listage, on peut arrêter là avec cette requête
        if request.unfounded_account :
            request.finished_date = datetime.now()
            continue
        
        # Si le listage des Tweets n'a pas commencé, on doit attendre un peu
        if not request.started_TwitterAPI_listing :
            if request.is_prioritary :
                shared_memory.scan_requests.step_D_TwitterAPI_index_account_tweets_prior_queue.put( request )
            else :
                shared_memory.scan_requests.step_D_TwitterAPI_index_account_tweets_queue.put( request )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_D_TwitterAPI_index_account_tweets_number" + str(thread_id), request )
        
        # Si on a vu cette requête il y a moins de 5 secondes, c'est qu'il n'y
        # a pas beaucoup de requêtes dans le pipeline, on peut donc dormir
        # 3 secondes, pour éviter de trop itérer dessus
        if time() - request.last_seen_TwitterAPI_indexer < 5 :
            sleep( 3 )
        request.last_seen_TwitterAPI_indexer = time()
        
        # On index / scan les comptes Twitter de la requête avec l'API Twitter
        if param.DEBUG :
            print( "[step_D_th" + str(thread_id) + "] Indexation des Tweets de @" + request.account_name + " trouvés par l'API Twitter." )
        request.finished_TwitterAPI_indexing = twitterapi_indexer.index_or_update_with_TwitterAPI(
                                                   request.account_name,
                                                   request.TwitterAPI_tweets_queue,
                                                   request.indexing_tweets,
                                                   add_step_D_times = shared_memory.execution_metrics.add_step_D_times )
        
        # Si l'indexation est terminée, on met la date de fin dans la requête
        if request.finished_TwitterAPI_indexing and not request.has_failed :
            print( "[step_D_th" + str(thread_id) + "] Fin de l'indexation des Tweets de @" + request.account_name + " trouvés par l'API Twitter." )
            
            # Enregistrer l'ID du Tweet trouvé le plus récent
            twitterapi_indexer.save_last_tweet_id( request.account_id, request.TwitterAPI_last_tweet_id )
            
            # Si les deux indexations ont terminé
            if request.finished_GOT3_indexing :
                # On indique la date de fin du scan
                request.finished_date = datetime.now()
                
                # On peut Màj les statistiques mises en cache dans l'objet
                # Shared_Memory
                shared_memory.tweets_count, shared_memory.accounts_count = bdd_direct_access.get_stats()
                
                # On peut supprimer l'objet Common_Tweet_IDs_List() pour gagner
                # de la mémoire vive
                request.indexing_tweets = None
                
                # Enregistrer le temps complet pour traiter cette requête
                shared_memory.execution_metrics.add_scan_request_full_time( time() - request.start )
        
        # Sinon, il faut la remettre dans notre file d'attente, si elle n'a pas
        # été marquée comme "has_failed", car si c'est le cas, cela veut dire
        # qu'un des deux threads de listage a planté, ou l'autre thread
        # d'indexation, et donc il vaut mieux arrêter.
        elif not request.has_failed :
            if request.is_prioritary :
                shared_memory.scan_requests.step_D_TwitterAPI_index_account_tweets_prior_queue.put( request )
            else :
                shared_memory.scan_requests.step_D_TwitterAPI_index_account_tweets_queue.put( request )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread.set_request( "thread_step_D_TwitterAPI_index_account_tweets_number" + str(thread_id), None )
    
    print( "[step_D_th" + str(thread_id) + "] Arrêté !" )
    return
