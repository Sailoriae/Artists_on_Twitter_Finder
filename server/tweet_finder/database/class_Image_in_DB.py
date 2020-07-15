#!/usr/bin/python3
# coding: utf-8

from typing import List


"""
Image dans la base de données
"""
class Image_in_DB :
    """
    @param account_id ID du compte Twitter ayant tweeté l'image
    @param tweet_id ID du Tweet contenant l'image
    @param image_features Liste des caractéristiques de l'image
    @param image_position La position de l'image (1-4) dans le Tweet (Car un
                          tweet peut contenir au maximum 4 images)
    """
    def __init__( self,
                 account_id : int,
                 tweet_id : int,
                 image_features : List[int],
                 image_position : int ) :
        self.account_id : int = account_id
        self.tweet_id : int = tweet_id
        self.image_features : List[int] = image_features
        self.image_position : int = image_position
        
        # Utilisé par le module "cbir_engine" pour stocker la distance entre
        # l'image de requête et cette image dans la base de données
        self.distance : int = None