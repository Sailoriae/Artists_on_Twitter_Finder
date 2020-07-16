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
ETAPE 4 du traitement d'une requête.
Thread d'indexation des tweets d'un compte Twitter en utilisant l'API publique
de Twitter, via la librairie Tweepy.
"""
def thread_step_4_TwitterAPI_index_account_tweets( thread_id : int, pipeline ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database( DEBUG = param.DEBUG )
    
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.step_4_TwitterAPI_index_account_tweets_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        pipeline.requests_in_thread[ "thread_step_4_TwitterAPI_index_account_tweets_number" + str(thread_id) ] = request
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        pipeline.set_request_to_next_step( request )
        
        # On index / scan les comptes Twitter de la requête avec l'API Twitter
        for twitter_account in request.twitter_accounts_with_id :
            print( "[step_4_th" + str(thread_id) + "] Indexation / scan du compte Twitter @" + twitter_account[0] + " avec l'API Twitter." )
            
            cbir_engine.index_or_update_with_TwitterAPI( twitter_account[0] )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        pipeline.requests_in_thread[ "thread_step_4_TwitterAPI_index_account_tweets_number" + str(thread_id) ] = None
        
        # On passe la requête à l'étape suivante
        # C'est la procédure pipeline.set_request_to_next_step qui vérifie si elle peut
        pipeline.set_request_to_next_step( request )
        
        # On dit qu'on a fini l'indexation pour les comptes de cette requête
        # On désactiver alors le bloquage mis lors de l'étape 2
        pipeline.indexing_done(
            [ data[1] for data in request.twitter_accounts_with_id ] )
    
    print( "[step_4_th" + str(thread_id) + "] Arrêté !" )
    return
