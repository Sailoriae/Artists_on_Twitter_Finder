#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep, time
from dateutil.tz import UTC

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    from os import getcwd as get_wdir
    from sys import path
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( "../.." )
    path.append(get_wdir())

import parameters as param
from link_finder.class_Link_Finder import Link_Finder
from link_finder.class_Link_Finder import Not_an_URL
from link_finder.class_Link_Finder import Unsupported_Website
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
from utils.class_Warnings_File import Warnings_File


"""
ETAPE 1 du traitement d'une requête.
Thread de Link Finder.
Cherche l'URL de l'illustration source, les comptes Twitter de l'artiste, et
les valide en cherchant leur ID.
"""
def thread_step_1_link_finder( thread_id : int, shared_memory ) :
    # Initialisation de notre moteur de recherche des comptes Twitter
    finder_engine = Link_Finder( DEBUG = param.DEBUG )
    
    # Ajouter à la liste des comptes disponibles le compte par défaut
    param.TWITTER_API_KEYS.append( { "OAUTH_TOKEN" : param.OAUTH_TOKEN,
                                     "OAUTH_TOKEN_SECRET" : param.OAUTH_TOKEN_SECRET,
                                     "AUTH_TOKEN" : None } )
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    twitter = TweepyAbstraction( param.API_KEY,
                                 param.API_SECRET,
                                 param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN"],
                                 param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN_SECRET"], )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_threads_registry = shared_memory.threads_registry
    shared_memory_user_requests = shared_memory.user_requests
    shared_memory_scan_requests = shared_memory.scan_requests
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_user_requests_step_1_link_finder_queue = shared_memory_user_requests.step_1_link_finder_queue
    
    # Dire qu'on ne fait rien
    shared_memory_threads_registry.set_request( f"thread_step_1_link_finder_th{thread_id}", None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_threads_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = shared_memory_user_requests_step_1_link_finder_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            request = None
        if request == None :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_1_link_finder_th{thread_id}", request )
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        shared_memory_user_requests.set_request_to_next_step( request )
        
        print( f"[step_1_th{thread_id}] Link Finder pour : {request.input_url}" )
        start = time()
        
        # Cette variable est mise à False si la requête ne peut pas aller plus
        # loin dans le pipeline utilisateur
        can_proceed = True
        
        # On lance le Link Finder sur cet URL
        try :
            data = finder_engine.get_data( request.input_url )
        
        # =====================================================================
        # VERIFICATION DE DONNES TROUVEES PAR LE LINK FINDER
        # =====================================================================
        
        # Si jamais l'entrée n'est pas une URL, on ne peut pas aller plus loin
        # avec cette requête (On passe donc son status à "Fin de traitement")
        except Not_an_URL :
            request.problem = "NOT_AN_URL"
            print( f"[step_1_th{thread_id}] Ceci n'est pas un URL !" )
            can_proceed = False
        
        # Si jamais le site n'est pas supporté, on ne va pas plus loin avec
        # cette requête (On passe donc son status à "Fin de traitement")
        except Unsupported_Website :
            request.problem = "UNSUPPORTED_WEBSITE"
            print( f"[step_1_th{thread_id}] Site non supporté !" )
            can_proceed = False
        
        # Si jamais l'URL de la requête est invalide, on ne va pas plus loin
        # avec elle (On passe donc son status à "Fin de traitement")
        if can_proceed and data == None :
            request.problem = "NOT_AN_ARTWORK_PAGE"
            print( f"[step_1_th{thread_id}] Le site est supporté, mais l'URL ne mène pas à une illustration." )
            can_proceed = False
        
        # Si jamais aucun compte Twitter n'a été trouvé, on ne va pas plus loin
        # avec la requête (On passe donc son status à "Fin de traitement")
        elif can_proceed and data.twitter_accounts == []:
            request.problem = "NO_TWITTER_ACCOUNT_FOUND"
            print( f"[step_1_th{thread_id}] Aucun compte Twitter trouvé pour l'artiste de cette illustration !" )
            can_proceed = False
        
        # Avoir trouvé plus de 10 comptes Twitter est étrange
        if can_proceed and len( data.twitter_accounts ) >= 10 :
            Warnings_File().write( f"Le Link Finder a trouvé {len(data.twitter_accounts)} comptes Twitter pour la requête suivante : {request.input_url}" )
        
        # On vérifie la liste des comptes Twitter
        if can_proceed :
            twitter_accounts_with_id = twitter.get_multiple_accounts_ids( data.twitter_accounts )
            filtered_twitter_accounts_with_id = []
            
            # On vérifie aussi que les comptes validés ne sont pas dans notre
            # liste noire (Dans ce cas, ils sont considérés comme invalides)
            for account_name, account_id in twitter_accounts_with_id :
                if not shared_memory_scan_requests.is_blacklisted( int( account_id ) ) :
                    filtered_twitter_accounts_with_id.append( ( account_name, account_id ) )
            
            request.twitter_accounts_with_id = filtered_twitter_accounts_with_id
        
        # Si jamais aucun compte Twitter valide n'a été trouvé, on ne va pas
        # plus loin avec la requête (On passe donc son status à "Fin de
        # traitement")
        if can_proceed and request.twitter_accounts_with_id == []:
            request.problem = "NO_VALID_TWITTER_ACCOUNT_FOUND"
            print( f"[step_1_th{thread_id}] Aucun compte Twitter valide trouvé pour l'artiste de cette illustration !" )
            can_proceed = False
        
        # =====================================================================
        # TERMINER LE TRAITEMENT
        # =====================================================================
        
        # Si la requête ne peut pas continuer dans le pipeline utilisateur
        if not can_proceed :
            # Forcer la fin de la requête, elle ne passe pas à l'étape suivante
            shared_memory_user_requests.set_request_to_next_step( request, force_end = True )
        
        # Si la requête peut continuer dans le pipeline utilisateur
        else :
            s = f"{'s' if len( request.twitter_accounts_with_id ) > 1 else ''}"
            print( f"[step_1_th{thread_id}] Compte{s} Twitter valide{s} trouvé{s} pour cet artiste : {', '.join( [ f'@{account[0]} (ID {account[1]})' for account in request.twitter_accounts_with_id ] )}" )
            print( f"[step_1_th{thread_id}] URL de l'image trouvée : {data.image_urls[0]}" )
            
            # Enregistrer les données trouvées dans l'objet User_Request
            # data.twitter_accounts a déjà été enregistré
            request.image_urls = data.image_urls
            request.utc_timestamp = data.publish_date.replace( tzinfo = UTC ).timestamp()
            
            # On passe la requête à l'étape suivante
            shared_memory_user_requests.set_request_to_next_step( request )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_1_link_finder_th{thread_id}", None )
        
        # Enregistrer le temps qu'on a mis pour traiter cette requête
        duration = time() - start
        shared_memory_execution_metrics.add_step_1_times( duration )
        
        # Un traitement de plus de 30 secondes est étrange
        if duration >= 30 :
            Warnings_File().write( f"La requête suivante a pris {duration} secondes dans le Link Finder : {request.input_url}" )
        
        # Forcer la fermeture du proxy
        request._pyroRelease()
    
    print( f"[step_1_th{thread_id}] Arrêté !" )
    return
