#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from tweet_finder import Reverse_Searcher


"""
ETAPE 3 du traitement d'une requête.
Thread de recherche d'image inversée.
Utilisation de l'indexation pour trouver le tweet de que l'artiste a posté avec
l'illustration de requête.
"""
def thread_step_3_reverse_search( thread_id : int, shared_memory ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = Reverse_Searcher( DEBUG = param.DEBUG, ENABLE_METRICS = param.ENABLE_METRICS)
    
    # Dire qu'on ne fait rien
    shared_memory.user_requests.requests_in_thread.set_request( "thread_step_3_reverse_search_number" + str(thread_id), None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = shared_memory.user_requests.step_3_reverse_search_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_3_reverse_search_number" + str(thread_id), request )
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        shared_memory.user_requests.set_request_to_next_step( request )
        
        if request.input_url != None :
            print( "[step_3_th" + str(thread_id) + "] Recherche de l'image suivante :\n" +
                   "[step_3_th" + str(thread_id) + "] " + request.input_url )
        else :
            print( "[step_3_th" + str(thread_id) + "] Recherche de l'image suivante :\n" +
                   "[step_3_th" + str(thread_id) + "] " + request.image_url )
        
        # On recherche les Tweets contenant l'image de requête
        # Et on les stocke dans l'objet de requête
        for twitter_account in request.twitter_accounts_with_id :
            print( "[step_3_th" + str(thread_id) + "] Recherche sur le compte Twitter @" + twitter_account[0] + "." )
            
            result = cbir_engine.search_tweet( request.image_url, account_name = twitter_account[0], add_step_3_times = shared_memory.execution_metrics.add_step_3_times )
            if result != None :
                request.founded_tweets += result
            else :
                print( "[step_3_th" + str(thread_id) + "] Erreur lors de la recherche d'image inversée." )
                request.problem = "ERROR_DURING_REVERSE_SEARCH"
        
        # Si il n'y a pas de compte Twitter dans la requête
        if request.twitter_accounts_with_id == []:
            print( "[step_3_th" + str(thread_id) + "] Recherche dans toute la base de données." )
            
            result = cbir_engine.search_tweet( request.image_url, add_step_3_times = shared_memory.execution_metrics.add_step_3_times )
            if result != None :
                request.founded_tweets += result
            else :
                print( "[step_3_th" + str(thread_id) + "] Erreur lors de la recherche d'image inversée." )
        
        # Trier la liste des résultats
        # On trie une liste d'objets par rapport à leur attribut "distance"
        request.founded_tweets = sorted( request.founded_tweets,
                                         key = lambda x: x.distance,
                                         reverse = False )
        
        # On ne garde que les 5 Tweets les plus proches
        request.founded_tweets = request.founded_tweets[:5]
        
        print( "[step_3_th" + str(thread_id) + "] Tweets trouvés (Du plus au moins proche) :\n" +
               "[step_3_th" + str(thread_id) + "] " + str( [ data.tweet_id for data in request.founded_tweets ] ) )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_3_reverse_search_number" + str(thread_id), None )
        
        # On passe la requête à l'étape suivante, fin du traitement
        # C'est la procédure shared_memory.user_requests.set_request_to_next_step
        # qui vérifie si elle peut
        shared_memory.user_requests.set_request_to_next_step( request )
    
    print( "[step_3_th" + str(thread_id) + "] Arrêté !" )
    return
