#!/usr/bin/python3
# coding: utf-8

import numpy as np
import urllib
import cv2


"""
Obtenir une image depuis une URL, et la convertir au bon format pour le moteur
de recherche d'image par le contenu.
"""
def url_to_cv2_image ( url : str ) -> np.ndarray :
    # Construire la requête
    request = urllib.request.Request( url )
    # Problème : Pour télécharger une image sur Pixiv, il faut que le champs
    # Referer de la requête soit Pixiv. Oui c'est nul. Donc on fait simple avec
    # cette petite bidouille, sans régex :
    if url[:20] == "https://i.pximg.net/" :
        request.add_header('Referer', 'https://www.pixiv.net/')
    # Télécharger l'image
    response = urllib.request.urlopen( request )
    # La convertir en array Numpy
    array = np.asarray( bytearray( response.read() ), dtype="uint8" )
    # La lire avec le format d'OpenCV
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
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
