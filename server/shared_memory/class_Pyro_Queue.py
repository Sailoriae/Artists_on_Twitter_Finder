#!/usr/bin/python3
# coding: utf-8

import Pyro4
import queue

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
    change_wdir( ".." )
    path.append(get_wdir())

from shared_memory.open_proxy import open_proxy


"""
Comme les files d'attentes contiennent des sémaphores, et qu'ils ne peuvent pas
être partagés, il faut faire cette couche pour qu'ils restent sur le serveur,
et ne soient pas transférés.
"""
@Pyro4.expose
class Pyro_Queue :
    """
    @param convert_uri Convertir les URI vers des Pyro4.Proxy, et inversement.
    """
    def __init__ ( self, convert_uri = False ) :
        self._convert_uri = convert_uri
        self._queue = queue.Queue()
    
    def get ( self, block = True ) :
        try :
            if self._convert_uri :
                return open_proxy( self._queue.get( block = block) )
            else :
                return self._queue.get( block = block)
        except queue.Empty :
            return None
    
    def put ( self, item ) :
        if self._convert_uri :
            self._queue.put( item.get_URI() )
        else :
            self._queue.put( item )
    
    def qsize ( self ) :
        return self._queue.qsize()
    
    @property
    def convert_uri ( self ) : return self._convert_uri
