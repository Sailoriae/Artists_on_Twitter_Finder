#!/usr/bin/python3
# coding: utf-8

import Pyro4


"""
Pour pouvoir insérer et sortir de la file des Tweets trouvés avec GOT3.
"""
@Pyro4.expose
class Pyro_GOT3_Tweet :
    def __init__ ( self, tweet_id, author_id, images_urls, hashtags ):
        self._id = tweet_id
        self._author_id = author_id
        self._images = images_urls
        self._hashtags = hashtags
    
    @property
    def id ( self ) : return self._id
    
    @property
    def author_id ( self ) : return self._author_id
    
    @property
    def images_urls ( self ) : return self._images_urls
    
    @property
    def hashtags ( self ) : return self._hashtags
