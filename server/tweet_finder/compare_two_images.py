#!/usr/bin/python3
# coding: utf-8

from PIL import Image, UnidentifiedImageError
from io import BytesIO
import requests
import urllib

import cv2
import numpy as np
from time import sleep, time

try :
    from utils import url_to_cv2_image
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .utils import url_to_cv2_image


"""
Obtenir l'image d'un Tweet, en gérant les erreurs communes qu'on peut
rencontrer.
"""
def get_tweet_image ( url ) :
    retry_count = 0
    while True :
        try :
            return Image.open(BytesIO(requests.get( url ).content))
        
        except urllib.error.HTTPError as error :
            if error.code == 404 or error.code == 500 or error.code == 403 : # Erreurs insolvables
                print( "[compare_two_images] Erreur avec l'image de Tweet suivante :", url )
                print( error )
                return None
            
            else :
                print( "[compare_two_images] Erreur avec l'image de Tweet suivante :", url )
                print( error )
                
                if error.code == 502 : # Il suffit d'attendre pour ce genre d'erreurs
                    if retry_count < 3 : # Essayer d'attendre, au maximum 3 coups
                        print( "[compare_two_images] On essaye d'attendre 10 secondes..." )
                        sleep( 10 )
                        retry_count += 1
                        continue
                
                elif retry_count < 1 : # Essayer un coup d'attendre
                    print( "[compare_two_images] On essaye d'attendre 10 secondes..." )
                    sleep( 10 )
                    retry_count += 1
                    continue
                
                raise error
        
        except UnidentifiedImageError as error :
            if retry_count < 1 : # Essayer un coup d'attendre
                print( "[compare_two_images] On essaye d'attendre 10 secondes..." )
                sleep( 10 )
                retry_count += 1
                continue
            
            raise error


"""
Comparer deux images et retourner le pourcentage de similitude.
@param url1 L'URL de la première image, ou un objet "PIL.Image".
@param url1 L'URL de la seconde image, ou un objet "PIL.Image".
@return Le pourcentage de similitude entre les deux images. Plus il est élevé,
        plus les images sont proches.
"""
def compare_two_images ( url1, url2, PRINT_METRICS = True ) :
    if isinstance( url1, str ) :
        img1 = get_tweet_image( url1 )
    else :
        img1 = url1
    
    if isinstance( url2, str ) :
        img2 = get_tweet_image( url2 )
    else :
        img2 = url2
    
    if PRINT_METRICS :
        start = time()
    
    # Si l'une des deux images est indisponible, on retourne 0%
    if img1 == None or img2 == None :
        return 0
    
    img1 = img1.convert("RGB")
    img2 = img2.convert("RGB")
    
    largeur_minimum = min( img1.size[0], img2.size[0] )
    hauteur_minimum = min( img1.size[1], img2.size[1] )
    img1 = img1.resize((largeur_minimum, hauteur_minimum))
    img2 = img2.resize((largeur_minimum, hauteur_minimum))
    
    # Source :
    # https://rosettacode.org/wiki/Percentage_difference_between_images
    assert img1.mode == img2.mode, "Different kinds of images."
    assert img1.size == img2.size, "Different sizes."
     
    pairs = zip(img1.getdata(), img2.getdata())
    if len(img1.getbands()) == 1:
        # For gray-scale JPEGs
        dif = sum(abs(p1-p2) for p1,p2 in pairs)
    else:
        dif = sum(abs(c1-c2) for p1,p2 in pairs for c1,c2 in zip(p1,p2))
     
    ncomponents = img1.size[0] * img1.size[1] * 3
    difference = 100 - (dif / 255.0 * 100) / ncomponents
    
    if PRINT_METRICS :
        print( "[compare_two_images] Temps de calcul :", time() - start )
    
    return difference


"""
Même fonction que la précédente, mais avec OpenCV.
Dure le même temps de traitement en moyenne !
@param url1 L'URL de la première image.
@param url1 L'URL de la seconde image.
@return Le pourcentage de similitude entre les deux images. Plus il est élevé,
        plus les images sont proches.
"""
def compare_two_images_with_opencv ( url1 : str, url2 : str, PRINT_METRICS = True ) :
    img1 = url_to_cv2_image( url1 )
    img2 = url_to_cv2_image( url2 )
    
    if PRINT_METRICS :
        start = time()
    
    largeur_minimum = min( img1.shape[0], img2.shape[0] )
    hauteur_minimum = min( img1.shape[1], img2.shape[1] )
    img1 = cv2.resize(img1, (largeur_minimum, hauteur_minimum))
    img2 = cv2.resize(img2, (largeur_minimum, hauteur_minimum))
    
    res = cv2.absdiff( img1, img2 )
    res = res.astype( np.uint8 )
    
    to_return = 100 - (np.count_nonzero(res) * 100) / res.size
    
    if PRINT_METRICS :
        print( "[compare_two_images] Temps de calcul:", time() - start )
    
    return to_return
