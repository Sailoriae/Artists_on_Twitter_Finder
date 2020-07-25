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
ETAPE 2 du traitement d'une requête.
Thread de listage des Tweets avec médias d'un compte Twitter, avec la librairie
GetOldTweets3.

Permet aussi de vérifier que les noms de comptes Twitter trouvés sont valides !
"""
def thread_step_2_GOT3_list_account_tweets( thread_id : int, pipeline ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database( DEBUG = param.DEBUG )
    
    # Accès direct à la base de données
    # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
    bdd_direct_access = SQLite_or_MySQL()
    
    # Dire qu'on ne fait rien
    pipeline.requests_in_thread[ "thread_step_2_GOT3_list_account_tweets_number" + str(thread_id) ] = None
    
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.step_2_GOT3_list_account_tweets_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        pipeline.requests_in_thread[ "thread_step_2_GOT3_list_account_tweets_number" + str(thread_id) ] = request
        
        # Si un un des ID des comptes Twitter de la requête est indiqué comme
        # en cours d'indexation, on remet cette requête en haut de la file
        # d'attente, nous permettant de traiter d'autres requêtes
        #
        # Ceci est possible si deux requêtes différentes ont le même compte
        # Twitter
        #
        # C'EST le THREAD DE L'ETAPE 4 QUI DESACTIVERA CE BLOQUAGE
        if pipeline.is_indexing( [ data[1] for data in request.twitter_accounts_with_id ] ) :
            # Dire qu'on n'est plus en train de traiter cette requête
            pipeline.requests_in_thread[ "thread_step_2_GOT3_list_account_tweets_number" + str(thread_id) ] = None
            
            # Remettre la requête dans la file d'attente
            pipeline.step_2_GOT3_list_account_tweets_queue.put( request )
            sleep( 1 )
            continue
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        pipeline.set_request_to_next_step( request )
        
        # On liste les tweets des comptes Twitter de la requête avec
        # GetOldTweets3
        for twitter_account in request.twitter_accounts_with_id :
            # Possibilité de sauter l'indexation des comptes déjà dans la BDD
            if request.intelligent_skip_indexing :
                if bdd_direct_access.is_account_indexed( twitter_account[1] ) :
                    print( "[step_2_th" + str(thread_id) + "] @" + twitter_account[0] + " est déjà dans la base de données." )
                    continue
            
            print( "[step_2_th" + str(thread_id) + "] Listage des tweets du compte Twitter @" + twitter_account[0] + " avec GetOldTweets3." )
            
            GOT3_list = cbir_engine.get_GOT3_list( twitter_account[0] )
            
            if GOT3_list != False : # Si entre le Link Finder et ce thread le compte est passé indisponible
                request.get_GOT3_list_result.append( ( twitter_account[0],
                                                       GOT3_list ) )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        pipeline.requests_in_thread[ "thread_step_2_GOT3_list_account_tweets_number" + str(thread_id) ] = None
        
        # On passe la requête à l'étape suivante
        # C'est la procédure pipeline.set_request_to_next_step qui vérifie si elle peut
        pipeline.set_request_to_next_step( request )
    
    print( "[step_2_th" + str(thread_id) + "] Arrêté !" )
    return
