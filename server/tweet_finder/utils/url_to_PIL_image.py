#!/usr/bin/python3
# coding: utf-8

from PIL import Image
from io import BytesIO

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

from tweet_finder.utils.url_to_content import url_to_content


"""
Convertir une image binaire au format de la librairie PIL.
"""
def binary_image_to_PIL_image ( image : bytes ) -> Image :
    return Image.open( BytesIO( image ) )


"""
Obtenir une image depuis une URL, et la convertir au format de la lib PIL.
"""
def url_to_PIL_image ( url : str ) -> Image :
    return binary_image_to_PIL_image( url_to_content( url ) )
