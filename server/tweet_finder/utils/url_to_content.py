#!/usr/bin/python3
# coding: utf-8

import urllib
import urllib.request

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


"""
Obtenir le contenu disponible à une URL.
Attention : Cette fonction retourne le contenu binaire !
"""
def url_to_content ( url : str ) -> bytes :
    # Construire la requête
    request = urllib.request.Request( url )
    
    # Problème : Pour télécharger une image sur Pixiv, il faut que le champs
    # Referer de la requête soit Pixiv. Oui c'est nul. Donc on fait simple avec
    # cette petite bidouille, sans régex :
    if url[:20] == "https://i.pximg.net/" :
        request.add_header("Referer", "https://www.pixiv.net/")
    
    request.add_header("User-Agent", param.USER_AGENT)
    
    # Télécharger et retourner le contenu
    return urllib.request.urlopen( request, timeout = 60 ).read()
