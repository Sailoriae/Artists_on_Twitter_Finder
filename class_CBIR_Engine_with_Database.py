#!/usr/bin/python3
# coding: utf-8

from cbir_engine import CBIR_Engine
from database import SQLite
from twitter import TweepyAbtraction
from utils import url_to_cv2_image
from typing import List
import parameters as param


"""
Moteur de recherche d'image par le contenu ("content-based image retrieval",
CBIR) qui indexe des tweets et les stocke dans sa base de données.

Les tweets doivent contenir au moins une image, sinon, ils seront rejetés.
Chaque image est stocké dans la base de données, associée à l'ID de son tweet,
l'ID de l'auteur du tweet, et la liste des caractéristiques extraites par le
moteur CBIR.
"""
class CBIR_Engine_with_Database :
    """
    Constructeur.
    Initialise le moteur CBIR, la couche d'abstraction à la base de données, et
    la couche d'abstraction à la librairie pour l'API Twitter.
    """
    def __init__( self, DEBUG : bool = False ) :
        self.DEBUG = DEBUG
        self.cbir_engine = CBIR_Engine()
        self.bdd = SQLite( param.SQLITE_DATABASE_NAME )
        self.twitter = TweepyAbtraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
    
    """
    Indexer les images d'un tweet dans la base de données.
    Chaque image est associée à l'ID de son tweet, l'ID de l'auteur du tweet
    et la liste des caractéristiques extraites par le moteur CBIR.
    
    @param tweet_id L'ID du tweet à indexer
    @return True si l'indexation a réussi
            False sinon
    """
    def index_tweet( self, tweet_id : int ) -> bool :
        tweet = self.twitter.get_tweet( tweet_id )
        
        if tweet == None :
            print( "Impossible d'indexer le Tweet " + str( tweet_id ) + "." )
            return False
        
        print( "Scan tweet " + str( tweet_id ) + "." )
        
        # Liste des URLs des images dans ce tweet
        tweet_images_url : List[str] = []
        
        try :
            for tweet_media in tweet._json["extended_entities"]["media"] :
                if tweet_media["type"] == "photo" :
                    tweet_images_url.append( tweet_media["media_url_https"] )
        except KeyError as error :
            if self.DEBUG :
                print( "Ce tweet n'a pas de médias." )
                print( error )
                return False
        
        if len( tweet_images_url ) == 0 :
            print( "Ce tweet n'a pas de médias." )
            return False
        
        if self.DEBUG :
            print( "Images trouvées dans le tweet " + str( tweet_id ) + " :" )
            print( str( tweet_images_url ) )
        
        for tweet_image_url in tweet_images_url :
            self.bdd.insert_tweet(
                tweet._json["user"]["id"],
                tweet_id,
                self.cbir_engine.index_cbir(
                    url_to_cv2_image( tweet_image_url )
                )
            )
        
        return True
    
    """
    Rechercher un tweet dans la base de donnée grâce à une image
    @param image_url L'URL de l'image à chercher
    @param account_id L'ID du compte Twitter dans lequel chercher (OPTIONNEL)
    @return Liste des ID de tweets contenant cette image
    """
    def search_tweet( self, image_url : str, account_id : int = 0 ) -> List[int] :
        return self.cbir_engine.search_cbir(
            url_to_cv2_image( image_url ),
            self.bdd.get_images_in_db_iterator( account_id )
        )


"""
Test du bon fonctionnement de cette classe

Note : Comment voir un tweet sur l'UI web avec son ID :
    https://twitter.com/any/status/1160998394887716864
"""
if __name__ == '__main__' :
    engine = CBIR_Engine_with_Database( DEBUG = True )
    index = engine.index_tweet( 1277396497789640704 )
    index = engine.index_tweet( 1160998394887716864 )
    index = engine.index_tweet( 1272649003570565120 )
    if index : print( "Test d'indexation OK." )
    else : print( "Erreur durant le test d'indexation !" )
    
    founded_tweets = engine.search_tweet(
        "https://pbs.twimg.com/media/EByx4lXUcAEzrly.jpg"
    )
    print( "Tweets contenant une image recherchée :")
    print( founded_tweets )
    if 1160998394887716864 in founded_tweets :
        print( "Test de recherche OK." )
    else :
        print( "Problème durant le test de recherche !" )
