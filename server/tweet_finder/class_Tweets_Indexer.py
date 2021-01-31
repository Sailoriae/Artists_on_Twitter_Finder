#!/usr/bin/python3
# coding: utf-8

from time import time
from statistics import mean
import queue

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( ".." )

from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.class_CBIR_Engine_for_Tweets_Images import CBIR_Engine_for_Tweets_Images


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
    @param FAILED_TWEETS_LIST Met dans cette liste les ID de Tweets ayant
                              au moins une image qui a échoué.
                              Les listes sont passées par référence.
    
    @return True si la file "tweets_queue" est terminée.
            False si il faut attendre un peu et rappeler cette méthode.
    """
    
    def index_tweets ( self, account_name, # Nom du compte, uniquement pour les print()
                             tweets_queue, # File d'attente d'entrée
                             indexing_tweets = None, # Objet de la mémoire partagée
                             add_step_C_or_D_times = None, # Fonction de la mémoire partagée
                             FORCE_INDEX = False,
                             FAILED_TWEETS_LIST = None ) -> bool :
#        if self.DEBUG :
#            print( f"[Index Tweets] Indexation / scan des Tweets de @{account_name} avec SearchAPI." )
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
                        print( f"[Index Tweets] {len(times)} Tweets indexés avec une moyenne de {mean(times)} secondes par Tweet." )
                        print( f"[Index Tweets] Temps moyens de calcul des caractéristiques : {mean(calculate_features_times)} secondes." )
                        print( f"[Index Tweets] Temps moyens d'enregistrement dans la BDD : {mean(insert_into_times)} secondes." )
                        if add_step_C_or_D_times != None :
                            add_step_C_or_D_times( times, calculate_features_times, insert_into_times )
                return False
            
            # Si on a atteint la fin de la file
            if tweet == None :
                if self.DEBUG or self.ENABLE_METRICS :
                    if len(times) > 0 :
                        print( f"[Index Tweets] {len(times)} Tweets indexés avec une moyenne de {mean(times)} secondes par Tweet." )
                        print( f"[Index Tweets] Temps moyens de calcul des caractéristiques : {mean(calculate_features_times)} secondes." )
                        print( f"[Index Tweets] Temps moyens d'enregistrement dans la BDD : {mean(insert_into_times)} secondes." )
                        if add_step_C_or_D_times != None :
                            add_step_C_or_D_times( times, calculate_features_times, insert_into_times )
                return True
            
            if self.DEBUG :
                print( f"[Index Tweets] Indexation Tweet ID {tweet['tweet_id']} de @{account_name}." )
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
            
            image_1_url = None
            image_2_url = None
            image_3_url = None
            image_4_url = None
            
            image_1_features = None
            image_2_features = None
            image_3_features = None
            image_4_features = None
            
            image_1_name = None
            image_2_name = None
            image_3_name = None
            image_4_name = None
            
            if self.DEBUG or self.ENABLE_METRICS :
                start_calculate_features = time()
            
            # Mis à True si le Tweet aura besoin d'être réindexé
            # Dans une liste, car les listes sont passées par référence
            will_need_retry = [False]
            
            # Traitement des images du Tweet
            if length > 0 :
                image_1_url = tweet["images"][0]
                image_1_features = self.engine.get_image_features( image_1_url, tweet["tweet_id"], CAN_RETRY = will_need_retry )
                image_1_name = image_1_url.replace( "https://pbs.twimg.com/media/", "" )
            if length > 1 :
                image_2_url = tweet["images"][1]
                image_2_features = self.engine.get_image_features( image_2_url, tweet["tweet_id"], CAN_RETRY = will_need_retry )
                image_2_name = image_2_url.replace( "https://pbs.twimg.com/media/", "" )
            if length > 2 :
                image_3_url = tweet["images"][2]
                image_3_features = self.engine.get_image_features( image_3_url, tweet["tweet_id"], CAN_RETRY = will_need_retry )
                image_3_name = image_3_url.replace( "https://pbs.twimg.com/media/", "" )
            if length > 3 :
                image_4_url = tweet["images"][3]
                image_4_features = self.engine.get_image_features( image_4_url, tweet["tweet_id"], CAN_RETRY = will_need_retry )
                image_4_name = image_4_url.replace( "https://pbs.twimg.com/media/", "" )
            
            if self.DEBUG or self.ENABLE_METRICS :
                calculate_features_times.append( time() - start_calculate_features )
                start_insert_into = time()
            
            # Stockage des résultats
            # On stocke même si toutes les images sont à None
            # Car cela veut dire que toutes les images ont étées perdues par Twitter
            self.bdd.insert_tweet(
                tweet["user_id"],
                tweet["tweet_id"],
                cbir_features_1 = image_1_features,
                cbir_features_2 = image_2_features,
                cbir_features_3 = image_3_features,
                cbir_features_4 = image_4_features,
                image_name_1 = image_1_name,
                image_name_2 = image_2_name,
                image_name_3 = image_3_name,
                image_name_4 = image_4_name,
                hashtags = tweet["hashtags"],
                FORCE_INDEX = FORCE_INDEX
            )
            
            # Si une image a échoué, le Tweet devra être réindexé
            # On le fait après le vrai enregistrement si jamais le compte
            # utilisé pour réindexé est bloqué par le compte Twitter en cours
            # de scan
            if will_need_retry[0] :
                self.bdd.add_retry_tweet(
                    tweet["tweet_id"],
                    tweet["user_id"],
                    image_1_url,
                    image_2_url,
                    image_3_url,
                    image_4_url,
                    tweet["hashtags"]
                )
                
                if FAILED_TWEETS_LIST != None :
                    # Bien mettre en INT au cas où, voir thread_retry_failed_tweets
                    FAILED_TWEETS_LIST.append( int( tweet["tweet_id"] ) )
            
            if self.DEBUG or self.ENABLE_METRICS :
                insert_into_times.append( time() - start_insert_into )
                times.append( time() - start )
