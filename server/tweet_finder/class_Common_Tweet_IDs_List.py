#!/usr/bin/python3
# coding: utf-8

import threading


"""
Objet commun aux deux indexer pour ne pas traiter un Tweet en même temps.
"""
class Common_Tweet_IDs_List :
    def __init__ ( self ) :
        self.sem = threading.Semaphore()
        self.tweet_ids_list = []
    
    """
    Dire qu'on est en train de traiter un Tweet.
    @param tweet_id L'ID du Tweet.
    @return True si l'ID n'est pas dans la liste, on peut traiter ce Tweet.
            False si l'ID est déjà dans la liste.
    """
    def add ( self, tweet_id : int ):
        self.sem.acquire()
        if tweet_id in self.tweet_ids_list :
            self.sem.release()
            return False
        self.tweet_ids_list.append( tweet_id )
        self.sem.release()
        return True
