#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from link_finder import Link_Finder
from tweet_finder.twitter import TweepyAbtraction
from tweet_finder.database import SQLite_or_MySQL


"""
ETAPE 1 du traitement d'une requête.
Thread de Link Finder.
"""
def thread_step_1_link_finder( thread_id : int, pipeline ) :
    # Initialisation de notre moteur de recherche des comptes Twitter
    finder_engine = Link_Finder()
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    twitter = TweepyAbtraction( param.API_KEY,
                                param.API_SECRET,
                                param.OAUTH_TOKEN,
                                param.OAUTH_TOKEN_SECRET )
    
    # Accès direct à la base de données
    # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
    bdd_direct_access = SQLite_or_MySQL()
    
    # Dire qu'on ne fait rien
    pipeline.requests_in_thread[ "thread_step_1_link_finder_number" + str(thread_id) ] = None
    
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.step_1_link_finder_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        pipeline.requests_in_thread[ "thread_step_1_link_finder_number" + str(thread_id) ] = request
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        pipeline.set_request_to_next_step( request )
        
        print( "[step_1_th" + str(thread_id) + "] Link Finder pour :\n" +
               "[step_1_th" + str(thread_id) + "] " + request.input_url )
        
        # On lance la recherche des comptes Twitter de l'artiste
        twitter_accounts = finder_engine.get_twitter_accounts( request.input_url )
        
        # Si jamais l'URL de la requête est invalide, on ne va pas plus loin
        # avec elle (On passe donc son status à "Fin de traitement")
        if twitter_accounts == None :
            # Dire qu'on n'est plus en train de traiter cette requête
            pipeline.requests_in_thread[ "thread_step_1_link_finder_number" + str(thread_id) ] = None
            
            request.problem = "INVALID_URL"
            request.set_status_done()
            
            print( "[step_1_th" + str(thread_id) + "] URL invalide ! Elle ne mène pas à une illustration." )
            continue
        
        # Si jamais le site n'est pas supporté, on ne va pas plus loin avec
        # cette requête (On passe donc son status à "Fin de traitement")
        elif twitter_accounts == False :
            # Dire qu'on n'est plus en train de traiter cette requête
            pipeline.requests_in_thread[ "thread_step_1_link_finder_number" + str(thread_id) ] = None
            
            request.problem = "UNSUPPORTED_WEBSITE"
            request.set_status_done()
            
            print( "[step_1_th" + str(thread_id) + "] Site non supporté !" )
            continue
        
        # Si jamais aucun compte Twitter n'a été trouvé, on ne va pas plus loin
        # avec la requête (On passe donc son status à "Fin de traitement")
        elif twitter_accounts == []:
            # Dire qu'on n'est plus en train de traiter cette requête
            pipeline.requests_in_thread[ "thread_step_1_link_finder_number" + str(thread_id) ] = None
            
            request.problem = "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            request.set_status_done()
            
            print( "[step_1_th" + str(thread_id) + "] Aucun compte Twitter trouvé pour l'artiste de cette illustration !" )
            continue
        
        # On vérifie la liste des comptes Twitter
        for account in twitter_accounts :
            account_id = twitter.get_account_id( account )
            if account_id != None :
                request.twitter_accounts_with_id.append( ( account, account_id ) )
        
        # Si jamais aucun compte Twitter valide n'a été trouvé, on ne va pas
        # plus loin avec la requête (On passe donc son status à "Fin de
        # traitement")
        if request.twitter_accounts_with_id == []:
            # Dire qu'on n'est plus en train de traiter cette requête
            pipeline.requests_in_thread[ "thread_step_1_link_finder_number" + str(thread_id) ] = None
            
            request.problem = "NO_VALID_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            request.set_status_done()
            
            print( "[step_1_th" + str(thread_id) + "] Aucun compte Twitter valide trouvé pour l'artiste de cette illustration !" )
            continue
        
        print( "[step_1_th" + str(thread_id) + "] Comptes Twitter trouvés pour cet artiste :\n" +
               "[step_1_th" + str(thread_id) + "] " + str( twitter_accounts ) )
        
        # Théoriquement, on a déjà vérifié que l'URL existe, donc on devrait
        # forcément trouver une image pour cette requête
        request.image_url = finder_engine.get_image_url( request.input_url )
        
        print( "[step_1_th" + str(thread_id) + "] URL de l'image trouvée :\n" +
               "[step_1_th" + str(thread_id) + "] " + request.image_url )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        pipeline.requests_in_thread[ "thread_step_1_link_finder_number" + str(thread_id) ] = None
        
        # Possibilité de sauter l'indexation si tous les comptes sont déjà dans
        # la base de données
        if request.intelligent_skip_indexing :
            check_list = []
            for twitter_account in request.twitter_accounts_with_id :
                check_list.append(
                    bdd_direct_access.is_account_indexed( twitter_account[1] )
                )
            if all( check_list ) :
                print( "[step_1_th" + str(thread_id) + "] Tous les comptes Twitter trouvés sont déjà dans la base de données, on saute les 3 étapes de mise à jour !" )
                pipeline.set_request_to_next_step( request )
                continue
        
        # On passe la requête à l'étape suivante
        # C'est la procédure pipeline.set_request_to_next_step qui vérifie si elle peut
        pipeline.set_request_to_next_step( request )
    
    print( "[step_1_th" + str(thread_id) + "] Arrêté !" )
    return
