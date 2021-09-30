#!/usr/bin/python3
# coding: utf-8

import urllib
import urllib.request


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
    
    request.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0")
    
    # Télécharger et retourner le contenu
    return urllib.request.urlopen( request ).read()
