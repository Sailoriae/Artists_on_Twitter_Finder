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

# Désactiver la comparaison des images durant l'étape 4 (Filtrage des résultats).
# Cela permet de gagner beaucoup de temps lors de l'éxécution des requêtes
# utilisateurs, car aucune image n'est téléchargée ni comparée.
# Cependant, il risque d'y avoir un peu plus de faux positifs, bien qu'on ne
# puisse pas estimer les proportions, car il n'y a pas de suite de test à AOTF.
# De toutes manières, l'algo de comparaison des images se trompe aussi sur les
# images en noir et blanc, comme les croquis ("sketches") par exemple.
# Donc laisser de préférence sur "True".
SKIP_IMAGES_COMPARAISON = True

if not USE_OPENCV :
    from PIL import Image, UnidentifiedImageError
    from io import BytesIO

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

from tweet_finder.compare_two_images import get_image

if USE_OPENCV :
    from tweet_finder.compare_two_images import compare_two_images_with_opencv
    from tweet_finder.utils.url_to_cv2_image import binary_image_to_cv2_image
else :
    from tweet_finder.compare_two_images import compare_two_images


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

Note : S'arrête si la distance du Khi-Carré s'éloigne de 0.5 de la première image
validée, ou si l'une des deux distance s'éloigne de x10 par rapport à la première
image, ou après 20 images validées.
"""
def thread_step_4_filter_results( thread_id : int, shared_memory ) :
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_threads_registry = shared_memory.threads_registry
    shared_memory_user_requests = shared_memory.user_requests
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_user_requests_step_4_filter_results_queue = shared_memory_user_requests.step_4_filter_results_queue
    
    # Dire qu'on ne fait rien
    shared_memory_threads_registry.set_request( f"thread_step_4_filter_results_th{thread_id}", None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = shared_memory_user_requests_step_4_filter_results_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_4_filter_results_th{thread_id}", request )
        
        # On passe la requête à l'étape suivante, c'est à dire notre étape
        shared_memory_user_requests.set_request_to_next_step( request )
        
        if param.ENABLE_METRICS :
            start = time()
            download_times = []
            compare_times = []
        
        # On utilise l'image téléchargée à l'étape 3
        if USE_OPENCV and not SKIP_IMAGES_COMPARAISON and request.found_tweets != [] :
            try :
                request_image = binary_image_to_cv2_image( request.query_image_as_bytes )
            except Exception as error :
                print( f"[step_3_th{thread_id}] Erreur lors du filtrage des résultats. Impossible d'obtenir l'image : {request.image_url}" )
                print( error )
                request.problem = "ERROR_DURING_REVERSE_SEARCH" # Un peu con de mettre la même erreur, mais bon
                
                shared_memory_threads_registry.set_request( f"thread_step_4_filter_results_th{thread_id}", None )
                shared_memory_user_requests.set_request_to_next_step( request )
                request.release_proxy()
                continue
        
        elif not SKIP_IMAGES_COMPARAISON and request.found_tweets != [] :
            try :
                request_image = Image.open(BytesIO( request.query_image_as_bytes ))
            
            # Si l'image a un format à la noix
            except UnidentifiedImageError as error:
                print( f"[step_3_th{thread_id}] L'image d'entrée est intraitable." )
                print( error )
                request.problem = "ERROR_DURING_REVERSE_SEARCH"
                
                shared_memory_threads_registry.set_request( f"thread_step_4_filter_results_th{thread_id}", None )
                shared_memory_user_requests.set_request_to_next_step( request )
                request.release_proxy()
                continue
        
        # On filtre la liste des images trouvées
        # Rappel : Cette liste est triée par distance durant l'étape 3
        # Rappel : Les distances sont dans l'ordre croissant
        new_found_tweets = [] # Nouvelle liste
        for image_in_db in request.found_tweets :
            if len(new_found_tweets) > 0 :
                # Si on s'éloigne de 0.5 de la première image ajoutée à la liste,
                # on peut arrêter là
                # On a déjà trouvé un Tweet avec l'image de toutes manières,
                # d'autres Tweets contenant l'image devraient être proches
                # A moins que Twitter aient changés leur algo de compression,
                # mais c'est pas grave (Ce qu'ils ont fait en 2019)
                if image_in_db.distance_chi2 - new_found_tweets[0].distance_chi2 > 0.5 :
                    break
                
                # Si l'une des deux distances fait x10 par rapport à la première
                # image validée, on peut arrêter là
                if ( image_in_db.distance_chi2 > new_found_tweets[0].distance_chi2 * 10 or
                     image_in_db.distance_bhattacharyya > new_found_tweets[0].distance_bhattacharyya * 10 ) :
                    break
                
                # Si on a déjà validé 20 images, on peut arrêter là
                if len(new_found_tweets) > 20 :
                    break
            
            # Détection de discorde entre la distance du test du Khi-Deux et celle de Bhattacharyya 
            # Lorsqu'il y a une image avec un Khi-Deux très petit, c'est signe que l'image d'entrée est un croquis
            # Si la distance de Bhattacharyya de cette même image est trop grande, c'est signe que le résultat n'est pas valide
            # Attention : NE PAS VIDER TOUS LES RESULTATS, ce n'est pas une bonne idée, par exemple pour @BaronEngel
            if image_in_db.distance_chi2 < 0.001 and image_in_db.distance_bhattacharyya > 0.1 :
                continue
            if image_in_db.distance_chi2 < 0.1 and image_in_db.distance_bhattacharyya > 0.2 :
                continue
            if image_in_db.distance_chi2 < 1 and image_in_db.distance_bhattacharyya > 0.25 :
                continue
            
            # Si on doit passer la comparaison des images
            if SKIP_IMAGES_COMPARAISON :
                new_found_tweets.append( image_in_db )
                continue
            
            if param.ENABLE_METRICS : start_download = time()
            found_image = get_image( "https://pbs.twimg.com/media/" + image_in_db.image_name )
            if param.ENABLE_METRICS : download_times.append( time() - start_download )
            
            # Les deux fonctions utilisent get_tweet_image(), donc prennent
            # bien les images de Tweets en qualité maximale !
            if param.ENABLE_METRICS : start_compare = time()
            if USE_OPENCV :
                similarity_percentage = compare_two_images_with_opencv( request_image, found_image, PRINT_METRICS = False )
            else :
                similarity_percentage = compare_two_images( request_image, found_image, PRINT_METRICS = False )
            if param.ENABLE_METRICS : compare_times.append( time() - start_compare )
            
            # Il faut que l'image trouvée et celle de requête se ressemblent à
            # au moins SEUIL en %
            if similarity_percentage > SEUIL :
                new_found_tweets.append( image_in_db )
        
        # On installe la nouvelle liste de résultats
        request.found_tweets = new_found_tweets
        
        print( f"[step_3_th{thread_id}] Tweets trouvés après filtrage (Du plus au moins proche) : {[ data.tweet_id for data in request.found_tweets ]}" )
        
        if param.ENABLE_METRICS :
            shared_memory_execution_metrics.add_step_4_times( time() - start, download_times, compare_times )
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_4_filter_results_th{thread_id}", None )
        
        # On passe la requête à l'étape suivante, fin du traitement
        shared_memory_user_requests.set_request_to_next_step( request )
        
        # Forcer la fermeture du proxy
        request.release_proxy()
    
    print( f"[step_3_th{thread_id}] Arrêté !" )
    return
