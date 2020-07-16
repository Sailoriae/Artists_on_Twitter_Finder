#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

from tweet_finder import CBIR_Engine_with_Database


"""
ETAPE 3 du traitement d'une requête.
Thread de recherche d'image inversée.
Utilisation de l'indexation pour trouver le tweet de que l'artiste a posté avec
l'illustration de requête.
"""
def thread_step_5_reverse_search( thread_id : int, pipeline ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database()
    
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.step_5_reverse_search_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        pipeline.requests_in_thread[ "thread_step_5_reverse_search_number" + str(thread_id) ] = request
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        pipeline.set_request_to_next_step( request )
        
        if request.input_url != None :
            print( "[step_5_th" + str(thread_id) + "] Recherche de l'image suivante :\n" +
                   "[step_5_th" + str(thread_id) + "] " + request.input_url )
        else :
            print( "[step_5_th" + str(thread_id) + "] Recherche de l'image suivante :\n" +
                   "[step_5_th" + str(thread_id) + "] " + request.image_url )
        
        # On recherche les Tweets contenant l'image de requête
        # Et on les stocke dans l'objet de requête
        for twitter_account in request.twitter_accounts :
            print( "[step_5_th" + str(thread_id) + "] Recherche sur le compte Twitter @" + twitter_account + "." )
            
            result = cbir_engine.search_tweet( request.image_url, twitter_account )
            if result != None :
                request.founded_tweets += result
            else :
                print( "[step_5_th" + str(thread_id) + "] Erreur lors de la recherche d'image inversée." )
                request.problem = "ERROR_DURING_REVERSE_SEARCH"
        
        # Si il n'y a pas de compte Twitter dans la requête
        if request.twitter_accounts == []:
            print( "[step_5_th" + str(thread_id) + "] Recherche dans toute la base de données." )
            
            result = cbir_engine.search_tweet( request.image_url )
            if result != None :
                request.founded_tweets += result
            else :
                print( "[step_5_th" + str(thread_id) + "] Erreur lors de la recherche d'image inversée." )
        
        # Trier la liste des résultats
        # On trie une liste d'objets par rapport à leur attribut "distance"
        request.founded_tweets = sorted( request.founded_tweets,
                                         key = lambda x: x.distance,
                                         reverse = False )
        
        print( "[step_5_th" + str(thread_id) + "] Tweets trouvés (Du plus au moins proche) :\n" +
               "[step_5_th" + str(thread_id) + "] " + str( [ data.tweet_id for data in request.founded_tweets ] ) )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        pipeline.requests_in_thread[ "thread_step_5_reverse_search_number" + str(thread_id) ] = None
        
        # On passe le status de la requête à "Fin de traitement"
        request.set_status_done()
    
    print( "[step_5_th" + str(thread_id) + "] Arrêté !" )
    return
