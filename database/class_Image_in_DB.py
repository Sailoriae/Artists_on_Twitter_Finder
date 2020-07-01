#!/usr/bin/python3
# coding: utf-8

from typing import List


"""
Image dans la base de données
"""
class Image_in_DB :
    def __init__( self,
                 account_id : int,
                 tweet_id : int,
                 image_features : List[int] ) :
        self.account_id : int = account_id
        self.tweet_id : int = tweet_id
        self.image_features : List[int] = image_features
        
        # Utilisé par le module "cbir_engine" pour identifier l'image
        self.identifier = self.tweet_id
