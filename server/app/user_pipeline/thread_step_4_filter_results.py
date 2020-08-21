#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep, time

# Utiliser OpenCV pour comparer deux images
# Note importante : Très peu testé, et nécessite un seuil très inférieur à 85%
# car OpenCV est plus précis que l'autre fonction, par exemple : 20-30%
# Donc laisser sur False pour la production
USE_OPENCV = False

# Il faut que l'image trouvée et celle de requête se ressemblent à au moins
# SEUIL, définit ci-dessous
if USE_OPENCV :
    SEUIL = 25 # pourcents
else :
    SEUIL = 85 # pourcents

if not USE_OPENCV :
    from PIL import Image, UnidentifiedImageError
    from io import BytesIO
    import requests

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param

if USE_OPENCV :
    from tweet_finder import compare_two_images_with_opencv
    from tweet_finder.utils import url_to_cv2_image
else :
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
        
        if param.ENABLE_METRICS :
            start = time()
        
        # On télécharge l'image de requête (Même si on l'a déjà fait lors de
        # la recherche inversée)
        if USE_OPENCV :
            try :
                request_image = url_to_cv2_image( request.image_url )
            except Exception as error :
                print( "[step_4_th" + str(thread_id) + "] Erreur lors du filtrage des résultats. Impossible d'obtenir l'image :", request.image_url )
                print( error )
                request.problem = "ERROR_DURING_REVERSE_SEARCH"
                
                shared_memory.user_requests.requests_in_thread.set_request( "thread_step_4_filter_results_number" + str(thread_id), None )
                shared_memory.user_requests.set_request_to_next_step( request )
                continue
        
        else :
            try :
                request_image = Image.open(BytesIO(requests.get( request.image_url ).content))
            
            # Si l'image a un format à la noix
            except UnidentifiedImageError :
                # On attend pour réessayer un coup
                # Mais vraiment, je ne sais pas pourquoi ça ne me sort pas
                # plutôt une erreur de réseau
                sleep( 10 )
                try :
                    request_image = Image.open(BytesIO(requests.get( request.image_url ).content))
                
                # Si ça veut pas, on arrête là
                except UnidentifiedImageError as error:
                    print( "[step_4_th" + str(thread_id) + "] Erreur lors du filtrage des résultats. Impossible d'obtenir l'image :", request.image_url )
                    print( error )
                    request.problem = "ERROR_DURING_REVERSE_SEARCH"
                    
                    shared_memory.user_requests.requests_in_thread.set_request( "thread_step_4_filter_results_number" + str(thread_id), None )
                    shared_memory.user_requests.set_request_to_next_step( request )
                    continue
        
        # On filtre la liste des images trouvées
        # Rappel : Cette liste est triée par distance durant l'étape 3
        # Rappel : Les distances sont dans l'ordre croissant
        new_founded_tweets = [] # Nouvelle liste
        for image_in_db in request.founded_tweets :
            if len(new_founded_tweets) > 0 :
                # Si on s'éloigne de 0.1 de la première image ajoutée à la liste,
                # on peut arrêter là
                # On a déjà trouvé un Tweet avec l'image de toutes manières,
                # d'autres Tweets contenant l'image devraient être proches
                # A moins que Twitter aient changés leur algo de compression,
                # mais c'est pas grave (Ce qu'ils ont fait en 2019)
                if image_in_db.distance - new_founded_tweets[0].distance > 0.1 :
                    break
            
            # Si a déjà trouvé quelque chose et que 
            
            image_url = "https://pbs.twimg.com/media/" + image_in_db.image_name
            if USE_OPENCV :
                similarity_percentage = compare_two_images_with_opencv( request_image, image_url, PRINT_METRICS = False )
            else :
                similarity_percentage = compare_two_images( request_image, image_url, PRINT_METRICS = False )
            
            # Il faut que l'image trouvée et celle de requête se ressemblent à
            # au moins SEUIL en %
            if similarity_percentage > 85 :
                new_founded_tweets.append( image_in_db )
        
        # On installe la nouvelle liste de résultats
        request.founded_tweets = new_founded_tweets
        
        print( "[step_4_th" + str(thread_id) + "] Tweets trouvés après filtrage (Du plus au moins proche) :\n" +
               "[step_4_th" + str(thread_id) + "] " + str( [ data.tweet_id for data in request.founded_tweets ] ) )
        
        if param.ENABLE_METRICS :
            shared_memory.execution_metrics.add_step_4_times( time() - start )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_4_filter_results_number" + str(thread_id), None )
        
        # On passe la requête à l'étape suivante, fin du traitement
        shared_memory.user_requests.set_request_to_next_step( request )
    
    print( "[step_4_th" + str(thread_id) + "] Arrêté !" )
    return
