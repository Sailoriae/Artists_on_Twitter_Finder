#!/usr/bin/python3
# coding: utf-8

import urllib

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

import utils.constants as const


# Taille maximale que AOTF peut télécharger
# Permet d'éviter de faire saturer la mémoire vive
MAX_SIZE = 20 * 1024 * 1024 # octets = 20 Mo

# Exception si jamais la taille maximale est dépassée
class File_Too_Big ( Exception ) :
    pass


"""
Obtenir le contenu disponible à une URL.
Attention : Cette fonction retourne le contenu binaire !

@param url URL où se situe le contenu à obtenir.
@param max_size Taille maximale (En octets) du contenu. Si cette taille est
                dépassée, le contenu ne sera pas téléchargé, et une erreur
                "File_Too_Big" sera émise.

@return Contenu binaire.
"""
def url_to_content ( url : str, max_size : int = MAX_SIZE ) -> bytes :
    # Construire la requête
    request = urllib.request.Request( url )
    
    # Problème : Pour télécharger une image sur Pixiv, il faut que le champs
    # Referer de la requête soit Pixiv. Oui c'est nul. Donc on fait simple avec
    # cette petite bidouille, sans régex :
    if url[:20] == "https://i.pximg.net/" :
        request.add_header("Referer", "https://www.pixiv.net/")
    
    # Ajouter notre "User-Agent" à la requête
    request.add_header("User-Agent", const.USER_AGENT)
    
    # Créer la requête (Ceci va faire une requête HTTP "HEAD")
    response = urllib.request.urlopen( request, timeout = 60 )
    
    # Vérifier la taille du contenu (Obtenu grâce au "HEAD")
    if response.length == None :
        raise File_Too_Big( f"Taille inconnue" )
    if response.length > max_size :
        raise File_Too_Big( f"{response.length/1024/1024} Mo contre {max_size/1024/1024} maximum" )
    
    # Télécharger et retourner le contenu
    return response.read()
