#!/usr/bin/python3
# coding: utf-8

from Pyro4 import Proxy
from types import MethodType

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

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
