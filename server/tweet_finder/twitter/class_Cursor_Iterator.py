#!/usr/bin/python3
# coding: utf-8

import tweepy
import time
from random import uniform


"""
Itérateur sur un curseur Tweepy. Permet de gèrer les erreurs 429.
tweepy.Cursor gère les Rate Limits, sauf les 429.
"""
class Cursor_Iterator :
    def __init__( self, tweepy_cursor ) :
        self._tweepy_cursor = tweepy_cursor

    def __iter__( self ) :
        return self
    
    def __next__( self ) :
        while True : # Solution très bourrin pour gèrer les 429
            retry_once = True
            
            try :
                return self._tweepy_cursor.__next__()
            
            # On peut se le permettre, car il enregistre ses curseurs après
            # avoir appelé la méthode, donc il crash avant d'avoir entregistré
            # les curseurs. Donc on peut rappeler "__next__()" en cas de crash.
            except tweepy.errors.HTTPException as error :
                    if error.response != None : # Si le serveur nous ferme la connexion au nez
                        if not error.response.status_code in [503, 429, 500] :
                            raise error
                    print( "[Tweepy Cursor_It] Limite atteinte, on réessaye dans environ 60 secondes..." )
                    print( error )
                    time.sleep( uniform( 50, 70 ) )
            
            except tweepy.errors.TwitterServerError as error :
                if retry_once :
                    time.sleep( 10 )
                    retry_once = False
                    continue
                raise error
