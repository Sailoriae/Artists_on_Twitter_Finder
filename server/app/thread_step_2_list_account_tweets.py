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
ETAPE 2, PARTIE 1/2 du traitement d'une requête.
Thread de listage des Tweets avec médias d'un compte Twitter.

Note importante : Ce thread doit être unique ! Il ne doit pas être exécuté
plusieurs fois.
En effet, il ne doit pas y avoir deux scans en même temps. Pour deux raisons :
- On pourrait scanner un même compte Twitter en même temps, deux fois donc,
- Et l'API Twitter nous bloque si on fait trop de requêtes.
"""
def list_account_tweets_thread_main( thread_id : int, pipeline ) :
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = CBIR_Engine_with_Database()
    
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.list_account_tweets_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Si un un des ID des comptes Twitter de la requête est indiqué comme
        # en cours de listage, on remet cette requête en haut de la file
        # d'attente, nous permettant de traiter d'autres requêtes
        #
        # Ceci est possible si deux requêtes différentes ont le même compte
        # Twitter
        if pipeline.is_listing( [ data[1] for data in request.twitter_accounts_with_id ] ) :
            pipeline.list_account_tweets_queue.put( request )
            sleep( 1 )
            continue
        
        # On passe le status de la requête à "En cours de traitement par un
        # thread de listage des tweets d'un compte Twitter"
        request.set_status_list_account_tweets()
        
        # On liste les tweets des comptes Twitter de la requête avec
        # GetOldTweets3
        for twitter_account in request.twitter_accounts :
            print( "[list_account_tweets_th" + str(thread_id) + "] Listage des tweets du compte Twitter @" + twitter_account + " avec GetOldTweets3." )
            
            GOT3_list = cbir_engine.get_GOT3_list( twitter_account )
            
            if GOT3_list == None :
                continue
            
            request.get_GOT3_list_result.append( ( twitter_account,
                                                   GOT3_list ) )
        
        # Si la liste des tweets trouvés par GetOldTweets3 et par l'API Twitter
        # sont vides, ça ne sert à rien de continuer !
        if request.get_GOT3_list_result == [] and request.get_TwitterAPI_list_result == [] :
            request.problem = "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            request.set_status_done()
            
            print( "[list_account_tweets_th" + str(thread_id) + "] Aucun compte Twitter valide !" )
            continue # On arrête là
        
        # On passe le status de la requête à "En attente de traitement par un
        # thread d'indexation des tweets d'un compte Twitter"
        request.set_status_wait_index_twitter_account()
        
        # On met la requête dans la file d'attente d'indexation des tweets d'un
        # compte Twitter
        # Si on est dans le cas d'une procédure complète
        if request.full_pipeline :
            pipeline.index_twitter_account_queue.put( request )
        
        # On dit qu'on a fini le listage pour les comptes de cette requête
        pipeline.listing_done(
            [ data[1] for data in request.twitter_accounts_with_id ] )
    
    print( "[list_account_tweets_th" + str(thread_id) + "] Arrêté !" )
    return
