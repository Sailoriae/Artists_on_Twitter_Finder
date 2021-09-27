#!/usr/bin/python3
# coding: utf-8

import urllib
import urllib.request
import numpy as np
import cv2


"""
Convertir une image binaire au bon format pour le moteur de recherche d'image
par le contenu.
"""
def binary_image_to_cv2_image ( image : bytes ) -> np.ndarray :
    # Convertir l'image en array Numpy
    array = np.asarray( bytearray( image ), dtype="uint8" )
    
    # La lire avec le format d'OpenCV
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    
    # La retourner
    return image


"""
Obtenir une image depuis une URL, et la convertir au bon format pour le moteur
de recherche d'image par le contenu.
"""
def url_to_cv2_image ( url : str ) -> np.ndarray :
    # Construire la requête
    request = urllib.request.Request( url )
    
    # Télécharger l'image
    response = urllib.request.urlopen( request ).read()
    
    # La lire avec OpenCV
    image = binary_image_to_cv2_image( response )
    
    # La retourner
    return image


"""
Test du bon fonctionnement de cette fonction
"""
if __name__ == '__main__' :
    image = url_to_cv2_image( "https://www.debian.org/Pics/openlogo-50.png" )
    type_img = type( image )
    if type_img == np.ndarray :
        print( f"OK : {type_img }" )
    else :
        print( f"Mauvais type : {type_img}" )
