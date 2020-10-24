#!/usr/bin/python3
# coding: utf-8

from time import time
from statistics import mean
from queue import Empty as Empty_Queue

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
class Tweets_Indexer_with_SearchAPI :
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
    Scanner tous les tweets d'un compte (Les retweets ne comptent pas).
    Seuls les tweets avec des médias seront scannés.
    Et parmis eux, seuls les tweets avec 1 à 4 images seront indexés.
    Cette méthode n'utilise pas l'API de timeline de Twitter, mais l'API de recherche,
    la même que pour https://twitter.com/search.
    
    Cette méthode ne recanne pas les tweets déjà scannés.
    En effet, elle commence sont analyse à la date du dernier scan.
    Si le compte n'a pas déjà été scanné, tous ses tweets le seront.
    
    C'est la méthode Tweets_Lister_with_SearchAPI.list_SearchAPI_tweets() qui
    vérifie si le nom de compte Twitter entré ici est valide !
    
    @param account_name Le nom d'utilisateur du compte à scanner, ne sert que à
                        faire des "print()".
    @param queue Fonction à appeler pour sortie les Tweets trouvés par
                 Tweet_Lister_with_SearchAPI.list_SearchAPI_tweets().
    @param indexing_tweets Objet "Common_Tweet_IDs_List" permettant d'éviter de
                           traiter le même Tweet en même temps quand on tourne
                           en parallèle de l'autre classe d'indexation.
    
    @return True si la file d'attente est terminée.
            False si il faut attendre un peu et rappeler cette méthode.
    """
    
    def index_or_update_with_SearchAPI ( self, account_name, queue_get, indexing_tweets, add_step_C_times = None ) -> bool :
#        if self.DEBUG :
#            print( "Indexation / scan des Tweets de @" + account_name + " avec SearchAPI." )
        if self.DEBUG or self.ENABLE_METRICS :
            times = [] # Liste des temps pour indexer un Tweet
            calculate_features_times = [] # Liste des temps pour calculer les caractéristiques des images du Tweet
            insert_into_times = [] # Liste des temps pour faire le INSERT INTO
        
        while True :
            try :
                tweet = queue_get( block = False )
            except Empty_Queue : # Si la queue est vide
                if self.DEBUG or self.ENABLE_METRICS :
                    if len(times) > 0 :
                        print( "[Index SearchAPI]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                        print( "[Index SearchAPI] Temps moyens de calcul des caractéristiques :", mean( calculate_features_times ) )
                        print( "[Index SearchAPI] Temps moyens d'enregistrement dans la BDD :", mean( insert_into_times ) )
                        if add_step_C_times != None :
                            add_step_C_times( times, calculate_features_times, insert_into_times )
                return False
            
            # Si on a atteint la fin de la file
            if tweet.id == None :
                if self.DEBUG or self.ENABLE_METRICS :
                    if len(times) > 0 :
                        print( "[Index SearchAPI]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                        print( "[Index SearchAPI] Temps moyens de calcul des caractéristiques :", mean( calculate_features_times ) )
                        print( "[Index SearchAPI] Temps moyens d'enregistrement dans la BDD :", mean( insert_into_times ) )
                        if add_step_C_times != None :
                            add_step_C_times( times, calculate_features_times, insert_into_times )
                return True
            
            if self.DEBUG :
                print( "[Index SearchAPI] Indexation Tweet " + str(tweet.id) + " de @" + account_name + "." )
            if self.DEBUG or self.ENABLE_METRICS :
                start = time()
            
            # Tester si l'autre classe d'indexation n'est pas déjà en train de
            # traiter, on n'a pas déjà traité, ce Tweet
            if not indexing_tweets.add( tweet.id ) :
                if self.DEBUG :
                    print( "[Index SearchAPI] Tweet déjà indexé par l'autre indexeur !" )
                continue
            
            # Tester avant d'indexer si le tweet n'est pas déjà dans la BDD
            if self.bdd.is_tweet_indexed( tweet.id ) :
                if self.DEBUG :
                    print( "Tweet déjà indexé !" )
                continue
            
            image_1 = None
            image_2 = None
            image_3 = None
            image_4 = None
            
            image_name_1 = None
            image_name_2 = None
            image_name_3 = None
            image_name_4 = None
            
            length = len( tweet.images )
            
            if length == 0 :
                if self.DEBUG :
                    print( "Tweet sans image, on le passe !" )
                continue
            
            if self.DEBUG or self.ENABLE_METRICS :
                start_calculate_features = time()
            
            # Traitement des images du Tweet
            if length > 0 :
                image_1 = self.engine.get_image_features(
                              tweet.images[0],
                              tweet.id )
                image_name_1 = tweet.images[0].replace("https://pbs.twimg.com/media/", "")
            if length > 1 :
                image_2 = self.engine.get_image_features(
                              tweet.images[1],
                              tweet.id )
                image_name_2 = tweet.images[1].replace("https://pbs.twimg.com/media/", "")
            if length > 2 :
                image_3 = self.engine.get_image_features(
                              tweet.images[2],
                              tweet.id )
                image_name_3 = tweet.images[2].replace("https://pbs.twimg.com/media/", "")
            if length > 3 :
                image_4 = self.engine.get_image_features(
                              tweet.images[3],
                              tweet.id )
                image_name_4 = tweet.images[3].replace("https://pbs.twimg.com/media/", "")
            
            # Si toutes les images du Tweet ont un problème
#            if image_1 == None and image_2 == None and image_3 == None and image_4 == None :
#                print( "Toutes les images du Tweet " + str(tweet.id) + " son inindexables !" )
#                continue
            
            if self.DEBUG or self.ENABLE_METRICS :
                calculate_features_times.append( time() - start_calculate_features )
            
            # Prendre les hashtags du Tweet
            # Fonctionne avec n'importe quel Tweet, même ceux entre 160 et 280
            # caractères (SearchAPI les voit en entier)
            hashtags = tweet.hashtags
            
            if self.DEBUG or self.ENABLE_METRICS :
                start_insert_into = time()
            
            # Stockage des résultats
            self.bdd.insert_tweet(
                tweet.author_id,
                tweet.id,
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
            
            if self.DEBUG or self.ENABLE_METRICS :
                insert_into_times.append( time() - start_insert_into )
                times.append( time() - start )
