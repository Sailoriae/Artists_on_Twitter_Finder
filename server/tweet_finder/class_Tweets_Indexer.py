#!/usr/bin/python3
# coding: utf-8

from time import time
from statistics import mean
import queue

try :
    from database import SQLite_or_MySQL
    from class_CBIR_Engine_for_Tweets_Images import CBIR_Engine_for_Tweets_Images
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .database import SQLite_or_MySQL
    from .class_CBIR_Engine_for_Tweets_Images import CBIR_Engine_for_Tweets_Images


# Très très très important :
# 1 - On analyse les images en qualité maximale.
# 2 - Si l'image n'est plus accessible, on remplit ses champs avec NULL !


"""
Classe permettant d'indexer les Tweets d'un compte Twitter trouvés avec l'API
de recherche de Twitter, via la librairie SNScrape.
"""
class Tweets_Indexer :
    def __init__( self, DEBUG : bool = False, ENABLE_METRICS : bool = False ) :
        self.DEBUG = DEBUG
        self.ENABLE_METRICS = ENABLE_METRICS
        self.bdd = SQLite_or_MySQL()
        self.engine = CBIR_Engine_for_Tweets_Images( DEBUG = DEBUG )
    
    """
    Enregistrer la date du Tweet listé le plus récent dans la base de données.
    Cette date est renvoyée par la méthode
    Tweet_Lister_with_SearchAPI.list_SearchAPI_tweets().
    
    @param last_tweet_date Date à enregistrer.
    @param account_id L'ID du compte Twitter.
    """
    def save_last_tweet_date ( self, account_id, last_tweet_date ) :
        self.bdd.set_account_SearchAPI_last_tweet_date( account_id, last_tweet_date )
    
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
    Indexer les Tweets trouvés par l'une des deux méthodes de listage :
    Tweets_Lister_with_SearchAPI.list_SearchAPI_tweets()
    Tweets_Lister_with_TimelineAPI.list_TimelineAPI_tweets()
    
    Ce sont ces méthodes qui vérifient que "account_name" est valide !
    
    @param account_name Le nom d'utilisateur du compte à scanner, ne sert que à
                        faire des "print()".
    @param tweets_queue Objet queue.Queue() où ont étés stockés les Tweets
                        trouvés par la méthode de listage.
    @param indexing_tweets Objet "Common_Tweet_IDs_List" permettant d'éviter
                           d'indexer le même Tweet en paralléle (OPTIONNEL).
    @param FORCE_INDEX Forcer l'ajout des Tweets. Efface ce qui a déjà été
                       enregistré (OPTIONNEL).
    
    @return True si la file "tweets_queue" est terminée.
            False si il faut attendre un peu et rappeler cette méthode.
    """
    
    def index_tweets ( self, account_name, # Nom du compte, uniquement pour les print()
                             tweets_queue, # File d'attente d'entrée
                             indexing_tweets = None, # Objet de la mémoire partagée
                             add_step_C_or_D_times = None, # Fonction de la mémoire partagée
                             FORCE_INDEX = False ) -> bool :
#        if self.DEBUG :
#            print( "Indexation / scan des Tweets de @" + account_name + " avec SearchAPI." )
        if self.DEBUG or self.ENABLE_METRICS :
            times = [] # Liste des temps pour indexer un Tweet
            calculate_features_times = [] # Liste des temps pour calculer les caractéristiques des images du Tweet
            insert_into_times = [] # Liste des temps pour faire le INSERT INTO
        
        while True :
            try :
                tweet = tweets_queue.get( block = False )
            except queue.Empty : # Si la file d'entrée est vide
                if self.DEBUG or self.ENABLE_METRICS :
                    if len(times) > 0 :
                        print( "[Index Tweets]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                        print( "[Index Tweets] Temps moyens de calcul des caractéristiques :", mean( calculate_features_times ) )
                        print( "[Index Tweets] Temps moyens d'enregistrement dans la BDD :", mean( insert_into_times ) )
                        if add_step_C_or_D_times != None :
                            add_step_C_or_D_times( times, calculate_features_times, insert_into_times )
                return False
            
            # Si on a atteint la fin de la file
            if tweet == None :
                if self.DEBUG or self.ENABLE_METRICS :
                    if len(times) > 0 :
                        print( "[Index Tweets]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                        print( "[Index Tweets] Temps moyens de calcul des caractéristiques :", mean( calculate_features_times ) )
                        print( "[Index Tweets] Temps moyens d'enregistrement dans la BDD :", mean( insert_into_times ) )
                        if add_step_C_or_D_times != None :
                            add_step_C_or_D_times( times, calculate_features_times, insert_into_times )
                return True
            
            if self.DEBUG :
                print( "[Index Tweets] Indexation Tweet " + str(tweet["tweet_id"]) + " de @" + account_name + "." )
            if self.DEBUG or self.ENABLE_METRICS :
                start = time()
            
            # Tester si ce Tweet n'a pas déjà été traité en paralléle
            if indexing_tweets != None :
                if not indexing_tweets.add( int( tweet["tweet_id"] ) ) :
                    if self.DEBUG :
                        print( "[Index Tweets] Tweet déjà indexé par un autre indexeur !" )
                    continue
            
            # Tester avant d'indexer si le tweet n'est pas déjà dans la BDD
            if self.bdd.is_tweet_indexed( tweet["tweet_id"] ) and not FORCE_INDEX :
                if self.DEBUG :
                    print( "[Index Tweets] Tweet déjà indexé !" )
                continue
            
            length = len( tweet["images"] )
            
            if length == 0 :
                if self.DEBUG :
                    print( "[Index Tweets] Tweet sans image, on le passe !" )
                continue
            
            image_1 = None
            image_2 = None
            image_3 = None
            image_4 = None
            
            image_1_name = None
            image_2_name = None
            image_3_name = None
            image_4_name = None
            
            if self.DEBUG or self.ENABLE_METRICS :
                start_calculate_features = time()
            
            # Traitement des images du Tweet
            if length > 0 :
                image_1 = self.engine.get_image_features( tweet["images"][0], tweet["tweet_id"] )
                image_1_name = tweet["images"][0].replace( "https://pbs.twimg.com/media/", "" )
            if length > 1 :
                image_2 = self.engine.get_image_features( tweet["images"][1], tweet["tweet_id"] )
                image_2_name = tweet["images"][1].replace( "https://pbs.twimg.com/media/", "" )
            if length > 2 :
                image_3 = self.engine.get_image_features( tweet["images"][2], tweet["tweet_id"] )
                image_3_name = tweet["images"][2].replace( "https://pbs.twimg.com/media/", "" )
            if length > 3 :
                image_4 = self.engine.get_image_features( tweet["images"][3], tweet["tweet_id"] )
                image_4_name = tweet["images"][3].replace( "https://pbs.twimg.com/media/", "" )
            
            if self.DEBUG or self.ENABLE_METRICS :
                calculate_features_times.append( time() - start_calculate_features )
                start_insert_into = time()
            
            # Stockage des résultats
            # On stocke même si toutes les images sont à None
            # Car cela veut dire que toutes les images ont étées perdues par Twitter
            self.bdd.insert_tweet(
                tweet["user_id"],
                tweet["tweet_id"],
                cbir_features_1 = image_1,
                cbir_features_2 = image_2,
                cbir_features_3 = image_3,
                cbir_features_4 = image_4,
                image_name_1 = image_1_name,
                image_name_2 = image_2_name,
                image_name_3 = image_3_name,
                image_name_4 = image_4_name,
                hashtags = tweet["hashtags"],
                FORCE_INDEX = FORCE_INDEX
            )
            
            if self.DEBUG or self.ENABLE_METRICS :
                insert_into_times.append( time() - start_insert_into )
                times.append( time() - start )
