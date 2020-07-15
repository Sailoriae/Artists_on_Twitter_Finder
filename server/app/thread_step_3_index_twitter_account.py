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
ETAPE 2, PARTIE 2/2 du traitement d'une requête.
Thread d'indexation des tweets d'un compte Twitter.

Note importante : Ce thread doit être unique ! Il ne doit pas être exécuté
plusieurs fois.
En effet, il ne doit pas y avoir deux scans en même temps. Pour deux raisons :
- On pourrait scanner un même compte Twitter en même temps, deux fois donc,
- Et l'API Twitter nous bloque si on fait trop de requêtes.
"""
def index_twitter_account_thread_main( thread_id : int, pipeline ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database()
    
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.index_twitter_account_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Si un un des ID des comptes Twitter de la requête est indiqué comme
        # en cours d'indexation, on remet cette requête en haut de la file
        # d'attente, nous permettant de traiter d'autres requêtes
        #
        # Ceci est possible si deux requêtes différentes ont le même compte
        # Twitter
        if pipeline.is_indexing( [ data[1] for data in request.twitter_accounts_with_id ] ) :
            pipeline.index_twitter_account_queue.put( request )
            sleep( 1 )
            continue
        
        # On passe le status de la requête à "En cours de traitement par un
        # thread d'indexation des tweets d'un compte Twitter"
        request.set_status_index_twitter_account()
        
        # On index / scan les comptes Twitter de la requête avec GetOldTweets3
        for (twitter_account, get_GOT3_list_result) in request.get_GOT3_list_result :
            print( "[index_twitter_account_th" + str(thread_id) + "] Indexation / scan du compte Twitter @" + twitter_account + " avec GetOldTweets3." )
            
            cbir_engine.index_or_update_all_account_tweets( twitter_account, get_GOT3_list_result )
        
        # On index / scan les comptes Twitter de la requête avec l'API Twitter
        for (twitter_account, get_TwitterAPI_list_result) in request.get_TwitterAPI_list_result :
            print( "[index_twitter_account_th" + str(thread_id) + "] Indexation / scan du compte Twitter @" + twitter_account + " avec l'API Twitter." )
            
            cbir_engine.index_or_update_with_TwitterAPI( twitter_account )
        
        # Vider la liste get_GOT3_list_result parce que c'est lourd et qu'on
        # en n'aura plus besoin
        request.get_GOT3_list_result = []
        
        # Vider la liste get_TwitterAPI_list_result parce que c'est lourd et qu'on
        # en n'aura plus besoin
        request.get_TwitterAPI_list_result = []
        
        # On passe le status de la requête à "En attente de traitement par un
        # thread de recherche d'image inversée"
        request.set_status_wait_reverse_search_thread()
        
        # On met la requête dans la file d'attente de la recherche d'image inversée
        # Si on est dans le cas d'une procédure complète
        if request.full_pipeline :
            pipeline.reverse_search_queue.put( request )
        
        # On dit qu'on a fini l'indexation pour les comptes de cette requête
        pipeline.indexing_done(
            [ data[1] for data in request.twitter_accounts_with_id ] )
    
    print( "[index_twitter_account_th" + str(thread_id) + "] Arrêté !" )
    return
