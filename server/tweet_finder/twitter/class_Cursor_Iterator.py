#!/usr/bin/python3
# coding: utf-8

import tweepy
import time
from random import randrange


"""
Itérateur sur un curseur Tweepy. Permet de gèrer les erreurs 429.
tweepy.Cursor gère les Rate Limits, sauf les 429.
"""
class Cursor_Iterator :
    def __init__( self, tweepy_cursor ) :
        self.tweepy_cursor = tweepy_cursor

    def __iter__( self ) :
        return self
    
    def __next__( self ) :
        retry_count = 0
        while True : # Solution très bourrin pour gèrer les 429
            try :
                return self.tweepy_cursor.__next__()
            except tweepy.error.TweepError as error :
                    if error.response.error != 503 and error.response.error != 429 :
                        raise error
                    print( "Limite atteinte, on réessaye dans environ 60 secondes..." )
                    print( error )
                    time.sleep( randrange( 50, 70 ) )
                    retry_count += 1
                    if retry_count > 30 :
                        raise error # Sera récupérée par le collecteur d'erreurs
