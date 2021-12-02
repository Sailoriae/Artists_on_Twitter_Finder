#!/usr/bin/python3
# coding: utf-8

from Pyro4 import Proxy
from types import MethodType

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
    change_wdir( ".." )
    path.append(get_wdir())

import parameters as param


"""
Méthode à ajouter à tous les objets qu'on renvoit.
"""
if param.ENABLE_MULTIPROCESSING :
    class Custom_Proxy ( Proxy ) :
        def get_URI ( self ) :
            return self._pyroUri.asString()
        def release_proxy ( self ) :
            self._pyroRelease()
else:
    def get_URI ( self ) :
        return self
    def release_proxy ( self ) :
        pass


"""
Si le multiprocessing est activé, ouvre un Proxy vers l'objet Pyro distant.
@param uri URI de l'objet Pyro distant.
@return Proxy vers cet objet distant.

Si le multiprocessing est désactivé, retourne simplement l'objet.
@param obj Objet à retourner.
@return Le même objet, non modifié.

Ne jamais ouvrir un proxy en appelant Pyro4.Proxy() ! Cela casserait la
désactivation du serveur Pyro si le serveur n'est pas exécuté en mode
multi-processus.
"""
if param.ENABLE_MULTIPROCESSING :
    def open_proxy ( uri : str ) :
        return Custom_Proxy( uri )
else :
    def open_proxy ( obj : object ) :
        obj.get_URI = MethodType( get_URI, obj )
        obj.release_proxy = MethodType( release_proxy, obj )
        return obj
