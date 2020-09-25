#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from link_finder import Link_Finder, Not_an_URL, Unsupported_Website
from tweet_finder.twitter import TweepyAbstraction


"""
ETAPE 1 du traitement d'une requête.
Thread de Link Finder.
Cherche l'URL de l'illustration source, les comptes Twitter de l'artiste, et
les valide en cherchant leur ID.
"""
def thread_step_1_link_finder( thread_id : int, shared_memory ) :
    # Initialisation de notre moteur de recherche des comptes Twitter
    finder_engine = Link_Finder()
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    twitter = TweepyAbstraction( param.API_KEY,
                                param.API_SECRET,
                                param.OAUTH_TOKEN,
                                param.OAUTH_TOKEN_SECRET )
    
    # Dire qu'on ne fait rien
    shared_memory.user_requests.requests_in_thread.set_request( "thread_step_1_link_finder_number" + str(thread_id), None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = shared_memory.user_requests.step_1_link_finder_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_1_link_finder_number" + str(thread_id), request )
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        shared_memory.user_requests.set_request_to_next_step( request )
        
        print( "[step_1_th" + str(thread_id) + "] Link Finder pour :\n" +
               "[step_1_th" + str(thread_id) + "] " + request.input_url )
        
        # On lance le Link Finder sur cet URL
        try :
            data = finder_engine.get_data( request.input_url )
        
        # Si jamais l'entrée n'est pas une URL, on ne peut pas aller plus loin
        # avec cette requête (On passe donc son status à "Fin de traitement")
        except Not_an_URL :
            request.problem = "NOT_AN_URL"
            shared_memory.user_requests.set_request_to_next_step( request, force_end = True )
            
            # Dire qu'on n'est plus en train de traiter cette requête
            shared_memory.user_requests.requests_in_thread.set_request( "thread_step_1_link_finder_number" + str(thread_id), None )
            
            print( "[step_1_th" + str(thread_id) + "] Ceci n'est pas une URL !" )
            continue
        
        # Si jamais le site n'est pas supporté, on ne va pas plus loin avec
        # cette requête (On passe donc son status à "Fin de traitement")
        except Unsupported_Website :
            request.problem = "UNSUPPORTED_WEBSITE"
            shared_memory.user_requests.set_request_to_next_step( request, force_end = True )
            
            # Dire qu'on n'est plus en train de traiter cette requête
            shared_memory.user_requests.requests_in_thread.set_request( "thread_step_1_link_finder_number" + str(thread_id), None )
            
            print( "[step_1_th" + str(thread_id) + "] Site non supporté !" )
            continue
        
        # Si jamais l'URL de la requête est invalide, on ne va pas plus loin
        # avec elle (On passe donc son status à "Fin de traitement")
        if data == None :
            request.problem = "INVALID_URL"
            shared_memory.user_requests.set_request_to_next_step( request, force_end = True )
            
            # Dire qu'on n'est plus en train de traiter cette requête
            shared_memory.user_requests.requests_in_thread.set_request( "thread_step_1_link_finder_number" + str(thread_id), None )
            
            print( "[step_1_th" + str(thread_id) + "] URL invalide ! Elle ne mène pas à une illustration." )
            continue
        
        # Si jamais aucun compte Twitter n'a été trouvé, on ne va pas plus loin
        # avec la requête (On passe donc son status à "Fin de traitement")
        elif data.twitter_accounts == []:
            request.problem = "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            shared_memory.user_requests.set_request_to_next_step( request, force_end = True )
            
            # Dire qu'on n'est plus en train de traiter cette requête
            shared_memory.user_requests.requests_in_thread.set_request( "thread_step_1_link_finder_number" + str(thread_id), None )
            
            print( "[step_1_th" + str(thread_id) + "] Aucun compte Twitter trouvé pour l'artiste de cette illustration !" )
            continue
        
        # On vérifie la liste des comptes Twitter
        for account in data.twitter_accounts :
            account_id = twitter.get_account_id( account )
            if account_id != None :
                request.twitter_accounts_with_id += [ ( account, account_id ) ] # Ne peut pas faire de append avec Pyro
        
        # Si jamais aucun compte Twitter valide n'a été trouvé, on ne va pas
        # plus loin avec la requête (On passe donc son status à "Fin de
        # traitement")
        if request.twitter_accounts_with_id == []:
            request.problem = "NO_VALID_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            shared_memory.user_requests.set_request_to_next_step( request, force_end = True )
            
            # Dire qu'on n'est plus en train de traiter cette requête
            shared_memory.user_requests.requests_in_thread.set_request( "thread_step_1_link_finder_number" + str(thread_id), None )
            
            print( "[step_1_th" + str(thread_id) + "] Aucun compte Twitter valide trouvé pour l'artiste de cette illustration !" )
            continue
        
        print( "[step_1_th" + str(thread_id) + "] Comptes Twitter valides trouvés pour cet artiste :\n" +
               "[step_1_th" + str(thread_id) + "] " + str( [ account[0] for account in request.twitter_accounts_with_id ] ) )
        
        # Théoriquement, on a déjà vérifié que l'URL existe, donc on devrait
        # forcément trouver une image pour cette requête
        request.image_url = data.image_url
        
        print( "[step_1_th" + str(thread_id) + "] URL de l'image trouvée :\n" +
               "[step_1_th" + str(thread_id) + "] " + request.image_url )
        
        # Même théorie, donc on devrait forcément trouver la date pour cette
        # requête
        request.datetime = data.publish_date
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_1_link_finder_number" + str(thread_id), None )
        
        # On passe la requête à l'étape suivante
        # C'est la procédure shared_memory.user_requests.set_request_to_next_step
        # qui vérifie si elle peut
        shared_memory.user_requests.set_request_to_next_step( request )
    
    print( "[step_1_th" + str(thread_id) + "] Arrêté !" )
    return
