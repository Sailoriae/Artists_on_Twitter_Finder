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
    def __init__( self, DEBUG : bool = False, DISPLAY_STATS : bool = False ) :
        self.DEBUG = DEBUG
        self.DISPLAY_STATS = DISPLAY_STATS
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
    @param queue Fonction à appeler pour sortie les Tweets trouvés par
                 Tweet_Lister_with_GetOldTweets3.list_GOT3_tweets().
    @param indexing_tweets Objet "Common_Tweet_IDs_List" permettant d'éviter de
                           traiter le même Tweet en même temps quand on tourne
                           en parallèle de l'autre classe d'indexation.
    
    @return True si la file d'attente est terminée.
            False si il faut attendre un peu et rappeler cette méthode.
    """
    
    def index_or_update_with_GOT3 ( self, account_name, queue_get, indexing_tweets, add_step_C_times = None ) -> bool :
#        if self.DEBUG :
#            print( "Indexation / scan des Tweets de @" + account_name + " avec GetOldTweets3." )
        if self.DEBUG or self.DISPLAY_STATS :
            times = [] # Liste des temps pour indexer un Tweet
            calculate_features_times = [] # Liste des temps pour calculer les caractéristiques des images du Tweet
            insert_into_times = [] # Liste des temps pour faire le INSERT INTO
        
        while True :
            try :
                tweet = queue_get( block = False )
            except Empty_Queue : # Si la queue est vide
                if self.DEBUG or self.DISPLAY_STATS :
                    if len(times) > 0 :
                        print( "[Index GOT3]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                        print( "[Index GOT3] Temps moyens de calcul des caractéristiques :", mean( calculate_features_times ) )
                        print( "[Index GOT3] Temps moyens d'enregistrement dans la BDD :", mean( insert_into_times ) )
                        if add_step_C_times != None :
                            add_step_C_times( times, calculate_features_times, insert_into_times )
                return False
            
            # Si on a atteint la fin de la file
            if tweet == None :
                if self.DEBUG or self.DISPLAY_STATS :
                    if len(times) > 0 :
                        print( "[Index GOT3]", len(times), "Tweets indexés avec une moyenne de", mean(times), "secondes par Tweet." )
                        print( "[Index GOT3] Temps moyens de calcul des caractéristiques :", mean( calculate_features_times ) )
                        print( "[Index GOT3] Temps moyens d'enregistrement dans la BDD :", mean( insert_into_times ) )
                        if add_step_C_times != None :
                            add_step_C_times( times, calculate_features_times, insert_into_times )
                return True
            
            if self.DEBUG :
                print( "[Index GOT3] Indexation Tweet " + str(tweet.id) + " de @" + account_name + "." )
            if self.DEBUG or self.DISPLAY_STATS :
                start = time()
            
            # Tester si l'autre classe d'indexation n'est pas déjà en train de
            # traiter, on n'a pas déjà traité, ce Tweet
            if not indexing_tweets.add( tweet.id ) :
                if self.DEBUG :
                    print( "[Index GOT3] Tweet déjà indexé par l'autre indexeur !" )
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
            
            length = len( tweet.images )
            
            if length == 0 :
                if self.DEBUG :
                    print( "Tweet sans image, on le passe !" )
                continue
            
            if self.DEBUG or self.DISPLAY_STATS :
                start_calculate_features = time()
            
            # Traitement des images du Tweet
            if length > 0 :
                image_1 = self.engine.get_image_features(
                              tweet.images[0],
                              tweet.id )
            if length > 1 :
                image_2 = self.engine.get_image_features(
                              tweet.images[1],
                              tweet.id )
            if length > 2 :
                image_3 = self.engine.get_image_features(
                              tweet.images[2],
                              tweet.id )
            if length > 3 :
                image_4 = self.engine.get_image_features(
                              tweet.images[3],
                              tweet.id )
            
            # Si toutes les images du Tweet ont un problème
            if image_1 == None and image_2 == None and image_3 == None and image_4 == None :
                print( "Toutes les images du Tweet " + str(tweet.id) + " son inindexables !" )
                continue
            
            if self.DEBUG or self.DISPLAY_STATS :
                calculate_features_times.append( time() - start_calculate_features )
            
            # Prendre les hashtags du Tweet
            # Fonctionne avec n'importe quel Tweet, même ceux entre 160 et 280
            # caractères (GOT3 les voit en entier)
            hashtags = tweet.hashtags.split(" ")
            
            if self.DEBUG or self.DISPLAY_STATS :
                start_insert_into = time()
            
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
            
            if self.DEBUG or self.DISPLAY_STATS :
                insert_into_times.append( time() - start_insert_into )
                times.append( time() - start )
