#!/usr/bin/python3
# coding: utf-8

import numpy as np
import cv2

from class_CBIR_Engine import CBIR_Engine, SEUIL_CHI2, SEUIL_BHATTACHARYYA

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

from utils import url_to_cv2_image


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
    print( "Khi-carré [0 -> +∞] :", d1 )
    print( "Bhattacharyya [0 -> 1] :", d2 )
    print( "Corrélation [1 -> 0] :", d3 )
    print( "Intersection [+∞ -> 0] :", d4 )
    print( "Euclidienne [0 -> +∞] :", d5 )
    print( "Manhattan [0 -> +∞] :", d6 )
    
    if d1 < SEUIL_CHI2 and d2 < SEUIL_BHATTACHARYYA :
        print( "Les images sont les mêmes." )
    else :
        print( "Les images ne sont pas les mêmes." )
