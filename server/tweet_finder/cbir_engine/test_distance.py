#!/usr/bin/python3
# coding: utf-8

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
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

from tweet_finder.cbir_engine.class_CBIR_Engine import CBIR_Engine, MAX_DIFFERENT_BITS
from tweet_finder.utils.url_to_PIL_image import url_to_PIL_image


"""
Ce script va faire calculer au moteur CBIR l'emprreinte de deux images, puis va
lancer la comparaison comme le ferait AOTF en exécution.
@param url1 URL de la première image.
@param url2 URL de la seconde image.
"""
def test_distance( url1, url2 ) :
    engine = CBIR_Engine()
    image1_hash = engine.index_cbir( url_to_PIL_image( url1 ) )
    image2_hash = engine.index_cbir( url_to_PIL_image( url2 ) )
    
    distance = engine._hamming_distance( image1_hash, image2_hash )
    print( "Nombre de bits de différence :", distance )
    
    if distance <= MAX_DIFFERENT_BITS :
        print( "Les images sont les mêmes." )
    else :
        print( "Les images ne sont pas les mêmes." )
