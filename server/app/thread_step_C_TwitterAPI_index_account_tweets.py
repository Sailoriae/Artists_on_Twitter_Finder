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
from tweet_finder.database import SQLite_or_MySQL


"""
ETAPE C du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread d'indexation des tweets d'un compte Twitter en utilisant l'API publique
de Twitter, via la librairie Tweepy.
"""
def thread_step_C_TwitterAPI_index_account_tweets( thread_id : int, shared_memory ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database( DEBUG = param.DEBUG )
    
    # Accès direct à la base de données
    # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
    bdd_direct_access = SQLite_or_MySQL()
    
    # Dire qu'on ne fait rien
    shared_memory.scan_requests.requests_in_thread[ "thread_step_C_TwitterAPI_index_account_tweets_number" + str(thread_id) ] = None
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory.scan_requests.step_C_TwitterAPI_index_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory.scan_requests.step_C_TwitterAPI_index_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                sleep( 1 )
                continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread[ "thread_step_C_TwitterAPI_index_account_tweets_number" + str(thread_id) ] = request
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        shared_memory.scan_requests.set_request_to_next_step( request )
        
        # On index / scan les comptes Twitter de la requête avec l'API Twitter
        print( "[step_C_th" + str(thread_id) + "] Indexation / scan du compte Twitter @" + request.account_name + " avec l'API Twitter." )
        cbir_engine.index_or_update_with_TwitterAPI( request.account_name )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.scan_requests.requests_in_thread[ "thread_step_C_TwitterAPI_index_account_tweets_number" + str(thread_id) ] = None
        
        # On passe la requête à l'étape suivante
        # C'est la procédure shared_memory.scan_requests.set_request_to_next_step
        # qui vérifie si elle peut
        shared_memory.scan_requests.set_request_to_next_step( request )
        
        # Comme on est le dernier thread de scan / analyse / indexation, on
        # peut Màj les statistiques mises en cache dans l'objet Pipeline
        shared_memory.tweets_count, shared_memory.accounts_count = bdd_direct_access.get_stats()
    
    print( "[step_C_th" + str(thread_id) + "] Arrêté !" )
    return