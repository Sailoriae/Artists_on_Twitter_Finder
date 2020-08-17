#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

from PIL import Image
from io import BytesIO
import requests

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

from tweet_finder import compare_two_images


"""
ETAPE 4 du traitement d'une requête.
Thread de filtrage des résultat de la recherche.
Compare les images trouvées par la recherche avec l'image de requête afin
d'être plus certain de trouver la bonne.

Permet d'éviter des faux positifs, qui sont nombreux à cause de la compression
des images sur les serveurs de Twitter. Et ils ne sont pas évitables, même en
augmentant la taille de l'histogramme lors de l'indexation. Il faut donc une
méthode indépendante de celle des histogrammes pour dire que deux images sont
les mêmes.
"""
def thread_step_4_filter_results( thread_id : int, shared_memory ) :
    # Dire qu'on ne fait rien
    shared_memory.user_requests.requests_in_thread.set_request( "thread_step_4_filter_results_number" + str(thread_id), None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = shared_memory.user_requests.step_4_filter_results_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_4_filter_results_number" + str(thread_id), request )
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        shared_memory.user_requests.set_request_to_next_step( request )
        
        # On télécharge l'image de requête (Même si on l'a déjà fait lors de
        # la recherche inversée)
        request_image = Image.open(BytesIO(requests.get( request.image_url ).content))
        
        # On filtre la liste des images trouvées
        new_founded_tweets = []
        for image_in_db in request.founded_tweets :
            image_url = "https://pbs.twimg.com/media/" + image_in_db.image_name
            similarity_percentage = compare_two_images( request_image, image_url )
            
            # Il faut que l'image trouvée et celle de requête se ressemblent à
            # au moins 85%
            if similarity_percentage > 85 :
                new_founded_tweets.append( image_in_db )
        
        # On installe la nouvelle liste de résultats
        request.founded_tweets = new_founded_tweets
        
        print( "[step_4_th" + str(thread_id) + "] Tweets trouvés après filtrage (Du plus au moins proche) :\n" +
               "[step_4_th" + str(thread_id) + "] " + str( [ data.tweet_id for data in request.founded_tweets ] ) )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_4_filter_results_number" + str(thread_id), None )
        
        # On passe la requête à l'étape suivante, fin du traitement
        shared_memory.user_requests.set_request_to_next_step( request )
    
    print( "[step_4_th" + str(thread_id) + "] Arrêté !" )
    return
