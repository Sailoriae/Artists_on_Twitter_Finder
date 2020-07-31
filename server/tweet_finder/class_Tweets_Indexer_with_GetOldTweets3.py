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

# Note importante :
# On peut télécharger les images des tweets donnés par GetOldTweets3 en
# meilleure qualité. Cependant, cela n'améliore pas de beaucoup la précision du
# calcul de la distance entre les images indexées et l'image de requête.
# En effet, il y a 4 niveaux de qualité sur Twitter : "thumb", "small",
# "medium" et "large". Et par défaut, si rien n'est indiqué, le serveur nous
# envoit la qualité "medium". Donc il n'y a pas une grande différence
# Laisser désactiver, car on ne sait pas s'il y a une qualité "large" pour
# toutes les images !
# De plus, laisser désactiver nous fait gagner un peu de connexion internet !
# Ca se sent bien sur les gros comptes !


"""
Classe permettant d'indexer les Tweets d'un compte Twitter trouvés avec la
librairie GetOldTweets3.
"""
class Tweets_Indexer_with_GetOldTweets3 :
    def __init__( self, DEBUG : bool = False ) :
        self.DEBUG = DEBUG
        self.bdd = SQLite_or_MySQL()
        self.engine = CBIR_Engine_for_Tweets_Images( DEBUG = DEBUG )
    
    """
    Enregistrer la date du Tweet listé le plus récent dans la base de données.
    Cette date est renvoyée par la méthode
    Tweet_Lister_with_GetOldTweets3.list_GOT3_tweets().
    
    @param last_tweet_date Date à enregistrer.
    @param account_id L'ID du compte Twitter.
    """
    def save_last_tweet_date ( self, account_id, last_tweet_date ) :
        self.bdd.set_account_GOT3_last_tweet_date( account_id, last_tweet_date )
    
    """
    Scanner tous les tweets d'un compte (Les retweets ne comptent pas).
    Seuls les tweets avec des médias seront scannés.
    Et parmis eux, seuls les tweets avec 1 à 4 images seront indexés.
    Cette méthode n'utilise pas l'API publique de Twitter, mais la librairie
    GetOldTweets3, qui utilise l'API de https://twitter.com/search.
    
    Cette méthode ne recanne pas les tweets déjà scannés.
    En effet, elle commence sont analyse à la date du dernier scan.
    Si le compte n'a pas déjà été scanné, tous ses tweets le seront.
    
    C'est la méthode Tweets_Lister_with_GetOldTweets3.list_GOT3_tweets() qui
    vérifie si le nom de compte Twitter entré ici est valide !
    
    @param account_name Le nom d'utilisateur du compte à scanner, ne sert que à
                        faire des "print()".
    @param queue La file d'attente donnée à la méthode
                 Tweet_Lister_with_GetOldTweets3.list_GOT3_tweets().
    
    @return True si la file d'attente est terminée.
            False si il faut attendre un peu et rappeler cette méthode.
    """
    
    def index_or_update_with_GOT3 ( self, account_name, queue ) -> bool :
        if self.DEBUG :
#            print( "Indexation / scan des Tweets de @" + account_name + " avec GetOldTweets3." )
            times = [] # Liste des temps pour indexer un Tweet
        
        while True :
            try :
                tweets = queue.get( block = False )
            except Empty_Queue : # Si la queue est vide
                if self.DEBUG :
                    if len(times) > 0 :
                        print( "[Index TwitAPI]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                break
            
            # Si on a atteint la fin de la file
            if tweets == None :
                if self.DEBUG :
                    if len(times) > 0 :
                        print( "[Index TwitAPI]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                return True
            
            for tweet in tweets :
                if self.DEBUG :
                    print( "[Index GOT3] Indexation Tweet " + str(tweet.id) + " de @" + account_name + "." )
                    start = time()
                
                # Tester avant d'indexer si le tweet n'est pas déjà dans la BDD
                if self.bdd.is_tweet_indexed( tweet.id ) :
                    if self.DEBUG :
                        print( "Tweet déjà indexé !" )
                    continue
                
                image_1 = None
                image_2 = None
                image_3 = None
                image_4 = None
                
                tweets_to_scan_length = len( tweet.images )
                
                if tweets_to_scan_length == 0 :
                    if self.DEBUG :
                        print( "Tweet sans image, on le passe !" )
                    continue
                
                # Traitement des images du Tweet
                if tweets_to_scan_length > 0 :
                    image_1 = self.engine.get_image_features(
                                  tweet.images[0],
                                  tweet.id )
                if tweets_to_scan_length > 1 :
                    image_2 = self.engine.get_image_features(
                                  tweet.images[1],
                                  tweet.id )
                if tweets_to_scan_length > 2 :
                    image_3 = self.engine.get_image_features(
                                  tweet.images[2],
                                  tweet.id )
                if tweets_to_scan_length > 3 :
                    image_4 = self.engine.get_image_features(
                                  tweet.images[3],
                                  tweet.id )
                
                # Si toutes les images du Tweet ont un problème
                if image_1 == None and image_2 == None and image_3 == None and image_4 == None :
                    print( "Toutes les images du Tweet " + str(tweet.id) + " son inindexables !" )
                    continue
                
                # Prendre les hashtags du Tweet
                # Fonctionne avec n'importe quel Tweet, même ceux entre 160 et 280
                # caractères (GOT3 les voit en entier)
                hashtags = tweet.hashtags.split(" ")
                
                # Stockage des résultats
                self.bdd.insert_tweet(
                    tweet.author_id,
                    tweet.id,
                    image_1,
                    image_2,
                    image_3,
                    image_4,
                    hashtags
                )
                
                if self.DEBUG :
                    times.append( time() - start )
