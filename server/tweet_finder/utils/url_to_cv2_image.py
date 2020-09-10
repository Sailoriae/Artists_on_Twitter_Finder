#!/usr/bin/python3
# coding: utf-8

import numpy as np
import cv2

try :
    from url_to_content import url_to_content
except ModuleNotFoundError :
    from .url_to_content import url_to_content


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
    # Télécharger l'image
    response = url_to_content( url )
    
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
        print( "OK : " + str( type_img ) )
    else :
        print( "Mauvais type : " + str( type_img ) )
