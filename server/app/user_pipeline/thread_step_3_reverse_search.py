#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep, time
import urllib
from PIL.Image import UnidentifiedImageError, DecompressionBombError

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
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
from tweet_finder.class_Reverse_Searcher import Reverse_Searcher
from tweet_finder.utils.url_to_content import url_to_content
from tweet_finder.utils.url_to_PIL_image import binary_image_to_PIL_image


"""
ETAPE 3 du traitement d'une requête.
Thread de recherche d'image inversée.
Utilisation de l'indexation pour trouver le tweet de que l'artiste a posté avec
l'illustration de requête.
"""
def thread_step_3_reverse_search( thread_id : int, shared_memory ) :
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_threads_registry = shared_memory.threads_registry
    shared_memory_user_requests = shared_memory.user_requests
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_user_requests_step_3_reverse_search_queue = shared_memory_user_requests.step_3_reverse_search_queue
    
    # Initialisation de notre moteur de recherche d'image par le contenu
    cbir_engine = Reverse_Searcher( DEBUG = param.DEBUG, ENABLE_METRICS = param.ENABLE_METRICS,
                                    add_step_3_times = shared_memory_execution_metrics.add_step_3_times )
    
    # Dire qu'on ne fait rien
    shared_memory_threads_registry.set_request( f"thread_step_3_reverse_search_th{thread_id}", None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = shared_memory_user_requests_step_3_reverse_search_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            request = None
        if request == None :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_3_reverse_search_th{thread_id}", request )
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        shared_memory_user_requests.set_request_to_next_step( request )
        
        if request.input_url != None :
            print( f"[step_3_th{thread_id}] Recherche de l'image suivante : {request.input_url}" )
        else :
            print( f"[step_3_th{thread_id}] Recherche de l'image suivante : {request.image_urls[0]}" )
        
        # Obtenir l'image et la charger en PIL.Image
        request_image_pil = None
        image_id = 0
        while True : # Pour tenter toutes les résolution d'images trouvées par le Link Finder
            try :
                # ATTENTION : Bien utiliser url_to_content(), car elle contient
                # une bidouille pour GET les image sur Pixiv
                query_image_as_bytes = url_to_content( request.image_urls[image_id] )
            except urllib.error.HTTPError as error : # On réessaye qu'une seule fois
                print( error )
                if error.code == 502 : # Et uniquement sur certaines erreurs
                    sleep(10)
                    query_image_as_bytes = url_to_content( request.image_urls[image_id] )
                else :
                    request.release_proxy()
                    raise error # Doit tomber dans le collecteur d'erreurs
            
            try :
                request_image_pil = binary_image_to_PIL_image( query_image_as_bytes )
            except UnidentifiedImageError as error :
                print( f"[step_3_th{thread_id}] L'image d'entrée est intraitable." )
                print( error )
                request.problem = "ERROR_DURING_REVERSE_SEARCH"
            except DecompressionBombError as error :
                print( f"[step_3_th{thread_id}] L'image d'entrée est trop grande." )
                print( error )
                if len(request.image_urls) > image_id :
                    image_id += 1 # Reboucler au "while True"
                    continue
                request.problem = "QUERY_IMAGE_TOO_BIG"
            
            break
        
        # Si on a réussi à obtenir l'image
        # Sinon, on va juste terminer la requête
        if request_image_pil != None :
            # On recherche les Tweets contenant l'image de requête
            # Et on les stocke dans l'objet de requête
            for twitter_account in request.twitter_accounts_with_id :
                print( f"[step_3_th{thread_id}] Recherche sur le compte Twitter @{twitter_account[0]}." )
                
                result = cbir_engine.search_tweet( request_image_pil,
                                                   account_name = twitter_account[0],
                                                   account_id = twitter_account[1] )
                if result != None :
                    request.found_tweets += result
            
            # Si il n'y a pas de compte Twitter dans la requête
            if request.twitter_accounts_with_id == []:
                print( f"[step_3_th{thread_id}] Recherche dans toute la base de données." )
                
                result = cbir_engine.search_tweet( request_image_pil )
                if result != None :
                    request.found_tweets += result
            
            # Trier la liste des résultats
            # Tri par la distance, puis si égalité par le nombre d'images dans
            # le Tweet, puis si encore égalité par l'ID du Tweet
            # Note : Les ID de Tweets sont dans l'ordre temporel
            # Source : https://stackoverflow.com/a/31951852
            request.found_tweets = sorted( request.found_tweets,
                                           key = lambda x: (x.distance, x.images_count, x.tweet_id),
                                           reverse = False )
            
            print( f"[step_3_th{thread_id}] Tweets trouvés (Du plus au moins proche) : {[ data.tweet_id for data in request.found_tweets ]}" )
        
        # Enregistrer le temps complet pour traiter cette requête
        shared_memory_execution_metrics.add_user_request_full_time( time() - request.start )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_3_reverse_search_th{thread_id}", None )
        
        # On passe la requête à l'étape suivante, fin du traitement
        shared_memory_user_requests.set_request_to_next_step( request )
        
        # Forcer la fermeture du proxy
        request.release_proxy()
    
    print( f"[step_3_th{thread_id}] Arrêté !" )
    return
