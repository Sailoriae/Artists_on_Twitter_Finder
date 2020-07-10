#!/usr/bin/python3
# coding: utf-8

import lib_GetOldTweets3 as GetOldTweets3

from cbir_engine import CBIR_Engine
from database import SQLite
from twitter import TweepyAbtraction
from utils import url_to_cv2_image
from typing import List
import parameters as param

# On peut télécharger les images des tweets donnés par GetOldTweets3 en
# meilleure qualité. Cependant, cela n'améliore pas de beaucoup la précision du
# calcul de la distance entre les images indexées et l'image de requête.
# En effet, il y a 4 niveaux de qualité sur Twitter : "thumb", "small",
# "medium" et "large". Et par défaut, si rien n'est indiqué, le serveur nous
# envoit la qualité "medium". Donc il n'y a pas une grande différence
# Laisser désactiver, car on ne sait pas s'il y a une qualité "large" pour
# toutes les images !
#from utils import add_argument_to_url


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
        
        image_1 = None
        image_2 = None
        image_3 = None
        image_4 = None
        
        length = len( tweet_images_url )
        
        if length == 0 :
            print( "Tweet sans image, on le passe !" )
            return False
        
        # Traitement des images du Tweet
        try :
            if length > 0 :
                image_1 = self.cbir_engine.index_cbir(
                              url_to_cv2_image( tweet_images_url[0] ) )
            if length > 1 :
                image_2 = self.cbir_engine.index_cbir(
                              url_to_cv2_image( tweet_images_url[1] ) )
            if length > 2 :
                image_3 = self.cbir_engine.index_cbir(
                              url_to_cv2_image( tweet_images_url[2] ) )
            if length > 3 :
                image_4 = self.cbir_engine.index_cbir(
                              url_to_cv2_image( tweet_images_url[3] ) )
        
        # Oui, c'est possible, Twitter n'est pas parfait
        # Exemple : https://twitter.com/apofissx/status/219051550696407040
        # Ce tweet est indiqué comme ayant une image, mais elle est en 404 !
        except Exception as error :
            print( error )
            return False
        
        # Stockage des résultats
        self.bdd.insert_tweet(
            tweet._json["user"]["id"],
            tweet_id,
            image_1,
            image_2,
            image_3,
            image_4,
        )
        
        return True
    
    """
    Scanner tous les tweets d'un compte (Les retweets ne comptent pas).
    Seuls les tweets avec des médias seront scannés.
    Et parmis eux, seuls les tweets avec 1 à 4 images seront indexés.
    Cette méthode n'utilise pas l'API publique de Twitter, mais la librairie
    GetOldTweets3, qui utilise l'API de https://twitter.com/search.
    
    Cette méthode ne recanne pas les tweets déjà scannés.
    En effet, elle commence sont analyse à la date du dernier scan.
    Si le compte n'a pas déjà été scanné, tous ses tweets le seront.
    
    @param account_name Le nom d'utilisateur du compte à scanner
                        Attention : Le nom d'utilisateur est ce qu'il y a après
                        le @ ! Par exemple : Si on veut scanner @jack, il faut
                        entrer dans cette fonction la chaine "jack".
    @return True si tout s'est bien passé
            False si le compte est introuvable
    """
    
    def index_or_update_all_account_tweets( self, account_name : str ) -> bool :
        account_id = self.twitter.get_account_id( account_name )
        if account_id == None :
            print( "Compte @" + account_name + " introuvable !" )
            return False
        
        # On scanne le compte depuis la dernière date dans la base de données,
        # ce qui nous renvoit la date de ce nouveau scan
        scan_date = self.index_all_account_tweets(
            account_name,
            since_date = self.bdd.get_account_last_scan( account_id )
        )
        
        # On met à jour la date du dernier scan dans la base de données
        if scan_date != None :
            self.bdd.set_account_last_scan( account_id, scan_date )
        
        return True
    
    """
    Même méthode que la précédente, mais ne prend pas elle-même la date du
    dernier scan dans la base de données.
    EVITER D'UTILISER CETTE METHODE !
    Sauf la précédente qui l'appelle.
    
    @param account_name Idem que dans la méthode précédente
    @param since_date Date du dernier scan, au format YYYY-MM-DD (OPTIONNEL).
                      Si cette date n'est pas indiquée, tous les tweets avec
                      média du compte seront scannés.
    @return Date du premier tweet scanné, c'est à dire le plus récent, au
            format YYYY-MM-DD.
            Ou None si aucun Tweet n'a été scanné !
    """
    def index_all_account_tweets( self, account_name : str, since_date : str = None ) :
        tweetCriteria = GetOldTweets3.manager.TweetCriteria()\
            .setQuerySearch( "from:" + account_name + " filter:media -filter:retweets" )
        
        if since_date != None :
            tweetCriteria.setSince( since_date )
        
        print( "Indexation / scan des Tweets de @" + account_name + "." )
        
        tweets_to_scan = GetOldTweets3.manager.TweetManager.getTweets(tweetCriteria)
        length = len( tweets_to_scan )
        
        # Stocker la date du premier tweet que l'on va scanner, c'est à dire le
        # plus récent
        scan_date = tweets_to_scan[0].date.strftime('%Y-%m-%d')
        
        print( str(length) + " Tweets à indexer." )
        
        for i in range( length ) :
            print( "Indexation tweet %s (%d/%d)." % ( tweets_to_scan[i].id, i+1, length) )
            
            image_1 = None
            image_2 = None
            image_3 = None
            image_4 = None
            
            tweets_to_scan_length = len( tweets_to_scan[i].images )
            
            if tweets_to_scan_length == 0 :
                print( "Tweet sans image, on le passe !" )
                continue
            
            # Traitement des images du Tweet
            try :
                if tweets_to_scan_length > 0 :
                    image_1 = self.cbir_engine.index_cbir(
                              url_to_cv2_image(
    #                              add_argument_to_url( tweets_to_scan[i].images[0], "name=large" ) ) )
                                  tweets_to_scan[i].images[0] ) )
                if tweets_to_scan_length > 1 :
                    image_2 = self.cbir_engine.index_cbir(
                              url_to_cv2_image(
    #                              add_argument_to_url( tweets_to_scan[i].images[1], "name=large" ) ) )
                                  tweets_to_scan[i].images[0] ) )
                if tweets_to_scan_length > 2 :
                    image_3 = self.cbir_engine.index_cbir(
                              url_to_cv2_image(
    #                              add_argument_to_url( tweets_to_scan[i].images[2], "name=large" ) ) )
                                  tweets_to_scan[i].images[0] ) )
                if tweets_to_scan_length > 3 :
                    image_4 = self.cbir_engine.index_cbir(
                              url_to_cv2_image(
    #                              add_argument_to_url( tweets_to_scan[i].images[3], "name=large" ) ) )
                                  tweets_to_scan[i].images[0] ) )
            
            # Oui, c'est possible, Twitter n'est pas parfait
            # Exemple : https://twitter.com/apofissx/status/219051550696407040
            # Ce tweet est indiqué comme ayant une image, mais elle est en 404 !
            except Exception as error :
                print( error )
                continue
            
            # Stockage des résultats
            self.bdd.insert_tweet(
                tweets_to_scan[i].author_id,
                tweets_to_scan[i].id,
                image_1,
                image_2,
                image_3,
                image_4,
            )
        
        return scan_date
    
    """
    Rechercher un tweet dans la base de donnée grâce à une image
    @param image_url L'URL de l'image à chercher
    @param account_name Le nom du compte Twitter dans lequel chercher, c'est à
                        dire ce qu'il y a après le @ (OPTIONNEL)
    @return Liste de tuples, contenant :
            - L'ID du Tweet contenant cette image (Parmis un maximum de 4
              images par Tweets)
            - La distance entre l'image de requête et l'image du Tweet
            None si il y a eu un problème
    """
    def search_tweet( self, image_url : str, account_name : str = None ) :
        if account_name != None :
            account_id = self.twitter.get_account_id( account_name )
        else :
            account_id = 0
        
        try :
            image = url_to_cv2_image( image_url )
        except Exception :
            print( "L'URL \"" + str(image_url) + "\" ne mène pas à une image !" )
            return None
        
        return self.cbir_engine.search_cbir(
            image,
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
    
    # Attention : Test vachement long, car il y a actuellement environ 2000
    # tweets sur ce compte, et que presque tous ont des médias
    engine.index_all_account_tweets( "MingjueChen" )
    
    founded_tweets = engine.search_tweet(
        "https://pbs.twimg.com/media/EByx4lXUcAEzrly.jpg"
    )
    print( "Tweets contenant une image recherchée :")
    print( founded_tweets )
    if 1160998394887716864 in [ data[0] for data in founded_tweets ] :
        print( "Test de recherche OK." )
    else :
        print( "Problème durant le test de recherche !" )
