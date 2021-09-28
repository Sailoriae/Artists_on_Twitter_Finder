#!/usr/bin/python3
# coding: utf-8

from time import time, sleep
from statistics import mean
import queue

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    from os import getcwd as get_wdir
    from sys import path
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( ".." )
    path.append(get_wdir())

from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.class_CBIR_Engine_for_Tweets_Images import CBIR_Engine_for_Tweets_Images
from shared_memory.open_proxy import open_proxy


# Très très très important :
# 1 - On analyse les images en qualité maximale.
# 2 - Si l'image n'est plus accessible, on remplit ses champs avec NULL !


"""
Classe permettant d'indexer n'importe quel Tweet, du moment qu'il est au format
renvoyé par la fonction "analyse_tweet_json()". Elle gère aussi les intructions
d'enregistrement des curseurs, données par les deux méthodes de listage :
- Tweets_Lister_with_SearchAPI.list_SearchAPI_tweets()
- Tweets_Lister_with_TimelineAPI.list_TimelineAPI_tweets()

Si je JSON d'instruction d'enregistrement contient le champs "request_uri", cela
indique la fin d'une requête de scan, et permet de mettre à jour les attributs
"finished_SearchAPI_indexing" ou "finished_TimelineAPI_indexing".

Si le JSON du Tweet contient le champs "was_failed_tweet" et que son indexation
réussie, il sera supprimé de la table "reindex_tweets". Ceci est une bidouille
pour le thread de retentative d'indexation.

Si le JSON du Tweet contient le champs "force_index", son éventuel
enregistrement dans la base de données sera écrasé.
Sinon, si le Tweet était déjà présent, il sera ignoré.

Note : Il n'y a aucun moyen pour empêcher deux threads indexeur (Donc éxécutant
en parallèle la fonction "index_tweets()") de traiter le même Tweet en même temps.
La probabilité que cela arrive est très faible, et implémenter des mesures contre
ferait perdre plus de temps qu'autre chose.
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
    Indexer les Tweets trouvés par les des deux méthodes de listage.
    Ce sont ces méthodes qui vérifient que "account_name" est valide !
    
    @param tweets_queue File d'attente où sont stockés les Tweets trouvés par
                        les méthode de listage.
    @param add_step_C_times Fonction de la mémoire partagée, objet
                            "Metrics_Container".
    @param keep_running Fonction de la mémoire partagée, objet "Shared_Memory".
    @param end_request Fonction de la mémoire partagée permettant de terminer
                       les requêtes de scan.
    @param current_tweet Liste vide permettant d'y place le JSON du Tweet en
                         cours d'indexation. Utile en cas de crash.
    """
    
    def index_tweets ( self, tweets_queue, # File d'attente d'entrée
                             add_step_C_times = None, # Fonction de la mémoire partagée
                             keep_running = None, # Fonction qui nous dit quand nous arrêter
                             end_request = None, # Fonction de la mémoire partagée permettant de terminer les requêtes de scan
                             current_tweet = [] # Permet de place le Tweet en cours d'indexation, utilisé en cas de crash
                       ) -> bool :
        if self.DEBUG or self.ENABLE_METRICS :
            times = [] # Liste des temps pour indexer un Tweet
            download_image_times = [] # Liste des temps pour télécharger les images d'un Tweet
            calculate_features_times = [] # Liste des temps pour d'éxécution du moteur CBIR pour une images d'un Tweet
            insert_into_times = [] # Liste des temps pour faire le INSERT INTO
        
        while keep_running == None or keep_running() :
            current_tweet.clear()
            try :
                tweet = tweets_queue.get( block = False )
            except queue.Empty :
                tweet = None
            if tweet == None :
                if keep_running == None : return
                sleep( 1 )
                continue
            
            # Enregistrer les mesures des temps d'éxécution tous les 100 Tweets.
            if len(times) >= 100 :
                print( f"[Tweets_Indexer] {len(times)} Tweets indexés avec une moyenne de {mean(times)} secondes par Tweet." )
                
                if len(download_image_times) > 0 :
                    print( f"[Tweets_Indexer] Temps moyens de téléchargement : {mean(download_image_times)} secondes." )
                if len(calculate_features_times) > 0 :
                    print( f"[Tweets_Indexer] Temps moyens de calcul dans le moteur CBIR : {mean(calculate_features_times)} secondes." )
                if len(insert_into_times) > 0 :
                    print( f"[Tweets_Indexer] Temps moyens d'enregistrement dans la BDD : {mean(insert_into_times)} secondes." )
                
                if add_step_C_times != None :
                    add_step_C_times( times, download_image_times, calculate_features_times, insert_into_times )
                
                times.clear()
                download_image_times.clear()
                calculate_features_times.clear()
                insert_into_times.clear()
            
            # Traiter les instructions d'enregistrement de curseurs
            if "save_SearchAPI_cursor" in tweet :
                self.save_last_tweet_date( tweet["account_id"], tweet["save_SearchAPI_cursor"] )
                if "request_uri" in tweet :
                    request = open_proxy( tweet["request_uri"] )
                    request.finished_SearchAPI_indexing = True
                    if end_request != None :
                        end_request( request, get_stats = self.bdd.get_stats() )
                    request.release_proxy()
                print( f"[Tweets_Indexer] Fin de l'indexation des Tweets de @{tweet['account_name']} trouvés avec l'API de recherche." )
                continue
            if "save_TimelineAPI_cursor" in tweet :
                self.save_last_tweet_id( tweet["account_id"], tweet["save_TimelineAPI_cursor"] )
                if "request_uri" in tweet :
                    request = open_proxy( tweet["request_uri"] )
                    request.finished_TimelineAPI_indexing = True
                    if end_request != None :
                        end_request( request, get_stats = self.bdd.get_stats() )
                    request.release_proxy()
                print( f"[Tweets_Indexer] Fin de l'indexation des Tweets de @{tweet['account_name']} trouvés avec l'API de timeline." )
                continue
            
            # A partir d'ici, on est certain qu'on traite le JSON d'un Tweet
            current_tweet.append( tweet )
            if self.DEBUG :
                print( f"[Tweets_Indexer] Indexation Tweet ID {tweet['tweet_id']} du compte ID {tweet['user_id']}." )
            if self.DEBUG or self.ENABLE_METRICS :
                start = time()
            
            # Pas besoin de tester si le Tweet est en train d'être traité en
            # parallèle, car la file "Tweets_to_Index_Queue" empêche qu'un
            # Tweet y soit présent deux fois
            
            # Tester avant d'indexer si le tweet n'est pas déjà dans la BDD
            # Ne jamais enlever cette vérification, il y a pleins de raisons
            # qui justifient de passer un peu de temps à toujours vérifier que
            # le Tweet existe, car sinon on perd trop de temps à faire le
            # calcul CBIR pour rien. Exemples de raisons :
            # - Le parallélisme et le fait qu'il n'y a pas d'objet dans la
            #   mémmoire partagée contenant tous les Tweets indexés,
            # - Le thread de reset des curseurs de listage avec SearchAPI.
            if self.bdd.is_tweet_indexed( tweet["tweet_id"] ) and not "force_index" in tweet :
                if self.DEBUG :
                    print( "[Tweets_Indexer] Tweet déjà indexé !" )
                continue
            
            length = len( tweet["images"] )
            
            if length == 0 :
                if self.DEBUG :
                    print( "[Tweets_Indexer] Tweet sans image, on le passe !" )
                continue
            
            image_1_url = None
            image_2_url = None
            image_3_url = None
            image_4_url = None
            
            image_1_hash = None
            image_2_hash = None
            image_3_hash = None
            image_4_hash = None
            
            image_1_name = None
            image_2_name = None
            image_3_name = None
            image_4_name = None
            
            # Mis à True si le Tweet aura besoin d'être réindexé
            # Dans une liste, car les listes sont passées par référence
            will_need_retry = [False]
            
            # Traitement des images du Tweet
            if length > 0 :
                image_1_url = tweet["images"][0]
                image_1_hash = self.engine.get_image_hash( image_1_url, tweet["tweet_id"], CAN_RETRY = will_need_retry,
                                                           download_image_times = download_image_times, calculate_features_times = calculate_features_times )
                image_1_name = image_1_url.replace( "https://pbs.twimg.com/media/", "" )
            if length > 1 :
                image_2_url = tweet["images"][1]
                image_2_hash = self.engine.get_image_hash( image_2_url, tweet["tweet_id"], CAN_RETRY = will_need_retry,
                                                           download_image_times = download_image_times, calculate_features_times = calculate_features_times )
                image_2_name = image_2_url.replace( "https://pbs.twimg.com/media/", "" )
            if length > 2 :
                image_3_url = tweet["images"][2]
                image_3_hash = self.engine.get_image_hash( image_3_url, tweet["tweet_id"], CAN_RETRY = will_need_retry,
                                                           download_image_times = download_image_times, calculate_features_times = calculate_features_times )
                image_3_name = image_3_url.replace( "https://pbs.twimg.com/media/", "" )
            if length > 3 :
                image_4_url = tweet["images"][3]
                image_4_hash = self.engine.get_image_hash( image_4_url, tweet["tweet_id"], CAN_RETRY = will_need_retry,
                                                           download_image_times = download_image_times, calculate_features_times = calculate_features_times )
                image_4_name = image_4_url.replace( "https://pbs.twimg.com/media/", "" )
            
            if self.DEBUG or self.ENABLE_METRICS :
                start_insert_into = time()
            
            # Stockage des résultats
            # On stocke même si toutes les images sont à None
            # Car cela veut dire que toutes les images ont étées perdues par Twitter
            self.bdd.insert_tweet(
                tweet["user_id"],
                tweet["tweet_id"],
                cbir_hash_1 = image_1_hash,
                cbir_hash_2 = image_2_hash,
                cbir_hash_3 = image_3_hash,
                cbir_hash_4 = image_4_hash,
                image_name_1 = image_1_name,
                image_name_2 = image_2_name,
                image_name_3 = image_3_name,
                image_name_4 = image_4_name,
                FORCE_INDEX = "force_index" in tweet
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
                )
            
            # Sinon, si c'était un Tweet échoué, on l'enlève de la tablee des
            # Tweets dont l'indexation a échouée
            # Ceci est la bidouille pour le thread de retentative d'indexation
            elif "was_failed_tweet" in tweet :
                self.bdd.remove_retry_tweet( tweet["tweet_id"] )
            
            if self.DEBUG or self.ENABLE_METRICS :
                insert_into_times.append( time() - start_insert_into )
                times.append( time() - start )
