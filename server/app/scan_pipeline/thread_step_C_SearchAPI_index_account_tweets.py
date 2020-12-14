#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep, time

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from tweet_finder import Tweets_Indexer
from tweet_finder.database import SQLite_or_MySQL


"""
ETAPE C du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread d'indexation des tweets d'un compte Twitter trouvés par le listage avec
l'API de recherche de Twitter.
"""
def thread_step_C_SearchAPI_index_account_tweets( thread_id : int, shared_memory ) :
    # Initialisation de l'indexeur de Tweets
    tweets_indexer = Tweets_Indexer( DEBUG = param.DEBUG, ENABLE_METRICS = param.ENABLE_METRICS )
    
    # Accès direct à la base de données
    # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
    bdd_direct_access = SQLite_or_MySQL()
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_threads_registry = shared_memory.threads_registry
    shared_memory_scan_requests = shared_memory.scan_requests
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_scan_requests_queues_sem = shared_memory_scan_requests.queues_sem
    shared_memory_scan_requests_step_C_SearchAPI_index_account_tweets_prior_queue = shared_memory_scan_requests.step_C_SearchAPI_index_account_tweets_prior_queue
    shared_memory_scan_requests_step_C_SearchAPI_index_account_tweets_queue = shared_memory_scan_requests.step_C_SearchAPI_index_account_tweets_queue
    
    # Dire qu'on ne fait rien
    shared_memory_threads_registry.set_request( f"thread_step_C_SearchAPI_index_account_tweets_number{thread_id}", None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_service_alive
        if not shared_memory_scan_requests_queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory_scan_requests_step_C_SearchAPI_index_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory_scan_requests_step_C_SearchAPI_index_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                shared_memory_scan_requests_queues_sem.release()
                sleep( 1 )
                continue
        
        # Dire qu'on est en train de traiter cette requête
        request.is_in_SearchAPI_indexing = True
        
        # Lacher le sémaphore
        shared_memory_scan_requests_queues_sem.release()
        
        # Si le compte est marqué comme introuvable par un des thread de
        # listage, on peut arrêter là avec cette requête
        if request.unfounded_account :
            # On appelle la méthode qui termine la requête
            shared_memory_scan_requests.end_request( request, None )
            request.release_proxy()
            continue
        
        # Si le listage des Tweets n'a pas commencé, on doit attendre un peu
        if not request.started_SearchAPI_listing :
            if request.is_prioritary :
                shared_memory_scan_requests_step_C_SearchAPI_index_account_tweets_prior_queue.put( request )
            else :
                shared_memory_scan_requests_step_C_SearchAPI_index_account_tweets_queue.put( request )
            request.release_proxy()
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_C_SearchAPI_index_account_tweets_number{thread_id}", request )
        
        # Si on a vu cette requête il y a moins de 5 secondes, c'est qu'il n'y
        # a pas beaucoup de requêtes dans le pipeline, on peut donc dormir
        # 3 secondes, pour éviter de trop itérer dessus
        if time() - request.last_seen_SearchAPI_indexer < 5 :
            sleep( 3 )
        request.last_seen_SearchAPI_indexer = time()
        
        # On index / scan les comptes Twitter de la requête avec l'API de recherche
        if param.DEBUG :
            print( f"[step_C_th{thread_id}] Indexation des Tweets de @{request.account_name} trouvés avec l'API de recherche." )
        request_SearchAPI_tweets_queue = request.SearchAPI_tweets_queue
        request_indexing_tweets = request.indexing_tweets
        request.finished_SearchAPI_indexing = tweets_indexer.index_tweets(
                                                  request.account_name,
                                                  request_SearchAPI_tweets_queue,
                                                  indexing_tweets = request_indexing_tweets,
                                                  add_step_C_or_D_times = shared_memory_execution_metrics.add_step_C_times )
        request_SearchAPI_tweets_queue.release_proxy()
        request_indexing_tweets.release_proxy()
        
        # Si l'indexation est terminée, on met la date de fin dans la requête
        if request.finished_SearchAPI_indexing and not request.has_failed :
            print( f"[step_C_th{thread_id}] Fin de l'indexation des Tweets de @{request.account_name} trouvés avec l'API de recherche." )
            
            # Enregistrer la date du Tweet trouvé le plus récent
            tweets_indexer.save_last_tweet_date( request.account_id, request.SearchAPI_last_tweet_date )
            
            # Si les deux indexations ont terminé
            if request.finished_TimelineAPI_indexing :
                # On appelle la méthode qui termine la requête
                shared_memory_scan_requests.end_request( request, bdd_direct_access.get_stats() )
        
        # Sinon, il faut la remettre dans notre file d'attente, si elle n'a pas
        # été marquée comme "has_failed", car si c'est le cas, cela veut dire
        # qu'un des deux threads de listage a planté, ou l'autre thread
        # d'indexation, et donc il vaut mieux arrêter.
        elif not request.has_failed :
            shared_memory_scan_requests_queues_sem.acquire()
            request.is_in_SearchAPI_indexing = False
            if request.is_prioritary :
                shared_memory_scan_requests_step_C_SearchAPI_index_account_tweets_prior_queue.put( request )
            else :
                shared_memory_scan_requests_step_C_SearchAPI_index_account_tweets_queue.put( request )
            shared_memory_scan_requests_queues_sem.release()
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_C_SearchAPI_index_account_tweets_number{thread_id}", None )
        
        # Forcer la fermeture du proxy
        request.release_proxy()
    
    print( f"[step_C_th{thread_id}] Arrêté !" )
    return
