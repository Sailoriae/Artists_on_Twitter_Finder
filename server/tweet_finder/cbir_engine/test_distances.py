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
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( "../.." )

from tweet_finder.cbir_engine.class_CBIR_Engine import CBIR_Engine, SEUIL_CHI2, SEUIL_BHATTACHARYYA
from tweet_finder.utils.url_to_cv2_image import url_to_cv2_image


"""
Ce script va faire calculer au moteur CBIR la liste des caractéristiques de
deux images, puis va lancer la comparaison comme le ferait le moteur.
@param url1 URL de la première image.
@param url2 URL de la seconde image.
"""
def test_distances( url1, url2 ) :
    engine = CBIR_Engine()
    image1_features = np.float32( engine.index_cbir( url_to_cv2_image( url1 ) ) )
    image2_features = np.float32( engine.index_cbir( url_to_cv2_image( url2 ) ) )
    
    # On prend le min(), car ce test est asymétrique
    d1 = min( cv2.compareHist( image1_features, image2_features, cv2.HISTCMP_CHISQR ),
              cv2.compareHist( image2_features, image1_features, cv2.HISTCMP_CHISQR ) )
    
    d2 = cv2.compareHist( image1_features, image2_features, cv2.HISTCMP_BHATTACHARYYA )
    
    d3 = cv2.compareHist( image1_features, image2_features, cv2.HISTCMP_CORREL )
    d4 = cv2.compareHist( image1_features, image2_features, cv2.HISTCMP_INTERSECT )
    d5 = cv2.norm( image1_features, image2_features, cv2.NORM_L2 )
    d6 = cv2.norm( image1_features, image2_features, cv2.NORM_L1 )
    
    print( "[Identiques -> Différentes]" )
    print( f"Khi-carré [0 -> +∞] : {d1}" )
    print( f"Bhattacharyya [0 -> 1] : {d2}" )
    print( f"Corrélation [1 -> 0] : {d3}" )
    print( f"Intersection [+∞ -> 0] : {d4}" )
    print( f"Euclidienne [0 -> +∞] : {d5}" )
    print( f"Manhattan [0 -> +∞] : {d6}" )
    
    if d1 < SEUIL_CHI2 and d2 < SEUIL_BHATTACHARYYA :
        print( "Les images sont les mêmes." )
    else :
        print( "Les images ne sont pas les mêmes." )
