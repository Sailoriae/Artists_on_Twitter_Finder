#!/usr/bin/python3
# coding: utf-8

import Pyro5.server
import threading


"""
Comme les sémaphores ne peuvent pas être partagés, il faut faire cette couche
pour qu'ils restent sur le serveur, et ne soient pas transférés.
"""
@Pyro5.server.expose
class Pyro_Semaphore :
    def __init__ ( self ) :
        self._sem = threading.Semaphore()
    
    def acquire ( self, timeout = None ) :
        return self._sem.acquire( timeout = timeout )
    
    def release ( self ) :
        self._sem.release()
