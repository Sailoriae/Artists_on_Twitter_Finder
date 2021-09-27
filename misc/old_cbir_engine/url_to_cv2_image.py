#!/usr/bin/python3
# coding: utf-8

import numpy as np
import cv2

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

from tweet_finder.utils.url_to_content import url_to_content


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
        print( f"OK : {type_img }" )
    else :
        print( f"Mauvais type : {type_img}" )
