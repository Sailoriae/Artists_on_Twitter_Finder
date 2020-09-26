#!/usr/bin/python3
# coding: utf-8

from time import time
from statistics import mean
from queue import Empty as Empty_Queue

try :
    from database import SQLite_or_MySQL
    from class_CBIR_Engine_for_Tweets_Images import CBIR_Engine_for_Tweets_Images
    from twitter import TweepyAbstraction
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .database import SQLite_or_MySQL
    from .class_CBIR_Engine_for_Tweets_Images import CBIR_Engine_for_Tweets_Images
    from .twitter import TweepyAbstraction

# Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
import parameters as param


"""
Classe permettant d'indexer les Tweets d'un compte Twitter trouvés avec l'API
de timeline de Twitter, via la librairie Tweepy.
"""
class Tweets_Indexer_with_TimelineAPI :
    def __init__( self, DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self.DEBUG = DEBUG
        self.ENABLE_METRICS = ENABLE_METRICS
        self.bdd = SQLite_or_MySQL()
        self.engine = CBIR_Engine_for_Tweets_Images( DEBUG = DEBUG )
        
        # Nécessaire si on passe des ID de Tweets à index_tweet()
        self.twitter = TweepyAbstraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
    
    """
    Enregistrer l'ID Tweet listé le plus récent dans la base de données.
    Cet ID est renvoyé par la méthode
    Tweets_Lister_with_TimelineAPI.list_TimelineAPI_tweets().
    
    @param last_tweet_id ID de Tweet à enregistrer.
    @param account_id L'ID du compte Twitter.
    """
    def save_last_tweet_id ( self, account_id, last_tweet_id ) :
        self.bdd.set_account_TimelineAPI_last_tweet_id( account_id, last_tweet_id )
    
    """
    Indexer les images d'un tweet dans la base de données.
    Chaque image est associée à l'ID de son tweet, l'ID de l'auteur du tweet
    et la liste des caractéristiques extraites par le moteur CBIR.
    
    @param tweet_id L'ID du tweet à indexer.
    @param tweepy_Status_object L'objet Status de la librairie Tweepy, écrase
                                le paramètre tweet_id (OPTIONNEL).
    @param FORCE_INDEX Forcer l'ajout des images si elles n'ont pas étés déjà
                       ajoutées.
    @return True si l'indexation a réussi,
            OU False sinon.
    """
    def index_tweet ( self, tweet_id : int, tweepy_Status_object = None, FORCE_INDEX = False ) -> bool :
        if tweepy_Status_object == None :
            tweet = self.twitter.get_tweet( tweet_id )
            
            if tweet == None :
                if self.DEBUG :
                    print( "Impossible d'indexer le Tweet " + str( tweet_id ) + "." )
                return False
        else :
            tweet = tweepy_Status_object
            tweet_id = tweet.id
        
        if self.DEBUG :
            print( "Scan tweet " + str( tweet_id ) + "." )
        
        # Tester avant d'indexer si le tweet n'est pas déjà dans la BDD
        if self.bdd.is_tweet_indexed( tweet_id ) and not FORCE_INDEX :
            if self.DEBUG :
                print( "Tweet déjà indexé !" )
            return True
        
        # Liste des URLs des images dans ce tweet
        tweet_images_url = []
        
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
            if self.DEBUG :
                print( "Ce tweet n'a pas de médias." )
            return False
        
        if self.DEBUG :
            print( "Images trouvées dans le tweet " + str( tweet_id ) + " :" )
            print( str( tweet_images_url ) )
        
        image_1 = None
        image_2 = None
        image_3 = None
        image_4 = None
        
        image_name_1 = None
        image_name_2 = None
        image_name_3 = None
        image_name_4 = None
        
        length = len( tweet_images_url )
        
        if length == 0 :
            if self.DEBUG :
                print( "Tweet sans image, on le passe !" )
            return False
        
        # Traitement des images du Tweet
        if length > 0 :
            image_1 = self.engine.get_image_features( tweet_images_url[0], tweet_id )
            image_name_1 = tweet_images_url[0].replace("https://pbs.twimg.com/media/", "")
        if length > 1 :
            image_2 = self.engine.get_image_features( tweet_images_url[1], tweet_id )
            image_name_2 = tweet_images_url[1].replace("https://pbs.twimg.com/media/", "")
        if length > 2 :
            image_3 = self.engine.get_image_features( tweet_images_url[2], tweet_id )
            image_name_3 = tweet_images_url[2].replace("https://pbs.twimg.com/media/", "")
        if length > 3 :
            image_4 = self.engine.get_image_features( tweet_images_url[3], tweet_id )
            image_name_4 = tweet_images_url[3].replace("https://pbs.twimg.com/media/", "")
        
        # Si toutes les images du Tweet ont un problème
        if image_1 == None and image_2 == None and image_3 == None and image_4 == None :
            print( "Toutes les images du Tweet " + str(tweet_id) + " son inindexables !" )
            return False
        
        # Prendre les hashtags
        try :
            hashtags = []
            for hashtag in tweet._json["entities"]["hashtags"] :
                # On ajoute le "#" car cette API de nous le met pas
                hashtags.append( "#" + hashtag["text"] )
        except KeyError as error :
            if self.DEBUG :
                print( "Erreur en récupérant les hashtags." )
                print( error )
            hashtags = None
        
        # Stockage des résultats
        self.bdd.insert_tweet(
            tweet._json["user"]["id"],
            tweet_id,
            image_1,
            image_2,
            image_3,
            image_4,
            image_name_1,
            image_name_2,
            image_name_3,
            image_name_4,
            hashtags
        )
        
        return True
    
    """
    Scanner tous les tweets d'un compte (Les retweets ne comptent pas).
    Seuls les tweets avec des médias seront scannés.
    Et parmis eux, seuls les tweets avec 1 à 4 images seront indexés.
    Cette méthode utilise l'API de timeline de Twitter, et est donc limitée au
    3200 premiers tweets (RT compris) d'un compte.
    
    Cette méthode ne recanne pas les tweets déjà scannés.
    En effet, elle commence sont analyse à la date du dernier scan.
    Si le compte n'a pas déjà été scanné, tous ses tweets le seront.
    
    C'est la méthode Tweets_Lister_with_TimelineAPI.list_TimelineAPI_tweets() qui
    vérifie si le nom de compte Twitter entré ici est valide !
    
    @param account_name Le nom d'utilisateur du compte à scanner, ne sert que à
                        faire des "print()".
    @param queue La file d'attente donnée à la méthode
                 Tweet_Lister_with_TimelineAPI.list_TimelineAPI_tweets().
    @param indexing_tweets Objet "Common_Tweet_IDs_List" permettant d'éviter de
                           traiter le même Tweet en même temps quand on tourne
                           en parallèle de l'autre classe d'indexation.
    
    @return True si la file d'attente est terminée.
            False si il faut attendre un peu et rappeler cette méthode.
    """
    def index_or_update_with_TimelineAPI ( self, account_name : str, queue, indexing_tweets, add_step_D_times = None ) -> bool :
#        if self.DEBUG :
#            print( "[Index TLAPI] Indexation de Tweets de @" + account_name + "." )
        if self.DEBUG  or self.ENABLE_METRICS :
            times = [] # Liste des temps pour indexer un Tweet
        
        while True :
            try :
                tweet = queue.get( block = False )
            except Empty_Queue : # Si la queue est vide
                if self.DEBUG or self.ENABLE_METRICS :
                    if len(times) > 0 :
                        print( "[Index TimelineAPI]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                        if add_step_D_times != None :
                            add_step_D_times( times )
                return False
            
            # Si on a atteint la fin de la file
            if tweet == None :
                if self.DEBUG or self.ENABLE_METRICS :
                    if len(times) > 0 :
                        print( "[Index TimelineAPI]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                        if add_step_D_times != None :
                            add_step_D_times( times )
                return True
            
            if self.DEBUG :
                print( "[Index TimelineAPI] Indexation Tweet " + str(tweet.id) + " de @" + account_name + "." )
            if self.DEBUG or self.ENABLE_METRICS :
                start = time()
            
            # Si il y a le champs "retweeted_status" dans le JSON
            if "retweeted_status" in tweet._json : # Le Tweet est un RT
                continue
            
            # Tester si l'autre classe d'indexation n'est pas déjà en train de
            # traiter, on n'a pas déjà traité, ce Tweet
            if not indexing_tweets.add( tweet.id ) :
                if self.DEBUG :
                    print( "[Index TimelineAPI] Tweet déjà indexé par l'autre indexeur !" )
                continue
            
            # Cela ne sert à rien tester avant d'indexer si le tweet n'est pas
            # déjà dans la BDD car la fonction index_tweet() le fait
            has_been_indexed = self.index_tweet( 0, tweepy_Status_object = tweet )
            
            if self.DEBUG or self.ENABLE_METRICS :
                if has_been_indexed :
                    times.append( time() - start )
