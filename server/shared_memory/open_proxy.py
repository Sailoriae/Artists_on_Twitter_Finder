#!/usr/bin/python3
# coding: utf-8

import Pyro5.client
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
Méthode à ajouter aux objets.
"""
if not param.ENABLE_MULTIPROCESSING :
    def _pyroRelease ( self ) :
        pass


"""
Si le multi-processus est activé, ouvre un Proxy vers l'objet Pyro distant.
@param uri URI de l'objet Pyro distant.
@return Proxy vers cet objet distant.

Si le multi-processus est désactivé, retourne simplement l'objet.
@param obj Objet à retourner.
@return Le même objet, non modifié.
        Il a en plus un attribut "_pyroUri" et une méthode "_pyroRelease()".

Ne jamais ouvrir un proxy en appelant Pyro5.client.Proxy() ! Cela casserait la
désactivation du serveur Pyro si le serveur n'est pas exécuté en mode
multi-processus.
"""
if param.ENABLE_MULTIPROCESSING :
    def open_proxy ( uri : str ) :
        return Pyro5.client.Proxy( uri )
else :
    def open_proxy ( obj : object ) :
        obj._pyroUri = obj
        obj._pyroRelease = MethodType( _pyroRelease, obj )
        return obj
