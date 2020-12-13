#!/usr/bin/python3
# coding: utf-8

import Pyro4
import queue

try :
    from open_proxy import open_proxy
except ModuleNotFoundError :
    from .open_proxy import open_proxy


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
        if self._convert_uri :
            return open_proxy( self._queue.get( block = block) )
        else :
            return self._queue.get( block = block)
    
    def put ( self, item ) :
        if self._convert_uri :
            self._queue.put( item.get_URI() )
        else :
            self._queue.put( item )
    
    def qsize ( self ) :
        return self._queue.qsize()
    
    @property
    def convert_uri ( self ) : return self._convert_uri
