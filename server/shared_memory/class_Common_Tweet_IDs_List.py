#!/usr/bin/python3
# coding: utf-8

import Pyro4
import threading


"""
Objet commun aux deux indexer pour ne pas traiter un Tweet en même temps.
"""
@Pyro4.expose
class Common_Tweet_IDs_List :
    def __init__ ( self ) :
        self._sem = threading.Semaphore()
        self._tweet_ids_list = []
    
    """
    Dire qu'on est en train de traiter un Tweet.
    @param tweet_id L'ID du Tweet.
    @return True si l'ID n'est pas dans la liste, on peut traiter ce Tweet.
            False si l'ID est déjà dans la liste.
    """
    def add ( self, tweet_id : int ) :
        self._sem.acquire()
        if tweet_id in self._tweet_ids_list :
            self._sem.release()
            return False
        self._tweet_ids_list.append( tweet_id )
        self._sem.release()
        return True
