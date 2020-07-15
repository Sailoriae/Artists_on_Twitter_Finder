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


"""
ETAPE 1 du traitement d'une requête.
Thread de Link Finder.
"""
def link_finder_thread_main( thread_id : int, pipeline ) :
    # Initialisation de notre moteur de recherche des comptes Twitter
    finder_engine = Link_Finder()
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    twitter = TweepyAbtraction( param.API_KEY,
                                param.API_SECRET,
                                param.OAUTH_TOKEN,
                                param.OAUTH_TOKEN_SECRET )
    
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = pipeline.link_finder_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # On passe le status de la requête à "En cours de traitement par un
        # thread de Link Finder"
        request.set_status_link_finder()
        
        print( "[link_finder_th" + str(thread_id) + "] Link Finder pour :\n" +
               "[link_finder_th" + str(thread_id) + "] " + request.input_url )
        
        # On lance la recherche des comptes Twitter de l'artiste
        twitter_accounts = finder_engine.get_twitter_accounts( request.input_url )
        
        # Si jamais l'URL de la requête est invalide, on ne va pas plus loin
        # avec elle (On passe donc son status à "Fin de traitement")
        if twitter_accounts == None :
            request.problem = "INVALID_URL"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] URL invalide ! Elle ne mène pas à une illustration." )
            continue
        
        # Si jamais le site n'est pas supporté, on ne va pas plus loin avec
        # cette requête (On passe donc son status à "Fin de traitement")
        elif twitter_accounts == False :
            request.problem = "UNSUPPORTED_WEBSITE"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] Site non supporté !" )
            continue
        
        # Si jamais aucun compte Twitter n'a été trouvé, on ne va pas plus loin
        # avec la requête (On passe donc son status à "Fin de traitement")
        elif twitter_accounts == []:
            request.problem = "NO_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] Aucun compte Twitter trouvé pour l'artiste de cette illustration !" )
            continue
        
        # Stocker les comptes Twitter trouvés
        request.twitter_accounts = twitter_accounts
        
        # On vérifie la liste des comptes Twitter
        for account in twitter_accounts :
            account_id = twitter.get_account_id( account )
            if account_id != None :
                request.twitter_accounts_with_id.append( ( account, account_id ) )
        
        # Si jamais aucun compte Twitter valide n'a été trouvé, on ne va pas
        # plus loin avec la requête (On passe donc son status à "Fin de
        # traitement")
        if twitter_accounts == []:
            request.problem = "NO_VALID_TWITTER_ACCOUNT_FOR_THIS_ARTIST"
            request.set_status_done()
            
            print( "[link_finder_th" + str(thread_id) + "] Aucun compte Twitter valide trouvé pour l'artiste de cette illustration !" )
            continue
        
        print( "[link_finder_th" + str(thread_id) + "] Comptes Twitter trouvés pour cet artiste :\n" +
               "[link_finder_th" + str(thread_id) + "] " + str( twitter_accounts ) )
        
        # Théoriquement, on a déjà vérifié que l'URL existe, donc on devrait
        # forcément trouver une image pour cette requête
        request.image_url = finder_engine.get_image_url( request.input_url )
        
        print( "[link_finder_th" + str(thread_id) + "] URL de l'image trouvée :\n" +
               "[link_finder_th" + str(thread_id) + "] " + request.image_url )
        
        # On passe le status de la requête à "En attente de traitement par un
        # thread de listage des tweets d'un compte Twitter"
        request.set_status_wait_list_account_tweets()
        
        # On met la requête dans la file d'attente de listage des tweets d'un
        # compte Twitter
        # Si on est dans le cas d'une procédure complète
        if request.full_pipeline :
            pipeline.list_account_tweets_queue.put( request )
    
    print( "[link_finder_th" + str(thread_id) + "] Arrêté !" )
    return
