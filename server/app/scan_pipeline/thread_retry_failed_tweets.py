#!/usr/bin/python3
# coding: utf-8

from time import sleep
import datetime
import queue

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param
from tweet_finder import Tweets_Indexer
from tweet_finder.analyse_tweet_json import analyse_tweet_json
from tweet_finder.database import SQLite_or_MySQL
from tweet_finder.twitter import TweepyAbstraction


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Thread qui retente d'indexer les Tweets dont l'indexation d'une image au moins
a échoué, c'est à dire que la méthode suivante a retourné "None" :
CBIR_Engine_for_Tweets_Images.get_image_features()
"""
def thread_retry_failed_tweets( thread_id : int, shared_memory ) :
    # Initialisation de l'indexeur de Tweets
    tweets_indexer = Tweets_Indexer( DEBUG = param.DEBUG, ENABLE_METRICS = param.ENABLE_METRICS )
    
    # Accès direct à la base de données
    bdd_direct_access = SQLite_or_MySQL()
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    # Ne devrait pas être utilisée en temps normal
    # Mais permet d'insérer manuellement des ID de Tweets dans la table "reindex_tweets"
    twitter = TweepyAbstraction( param.API_KEY,
                                 param.API_SECRET,
                                 param.OAUTH_TOKEN,
                                 param.OAUTH_TOKEN_SECRET )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        # Prendre l'itérateur sur les Tweets à réessayer, triés dans l'ordre du
        # moins récemment réessayé au plus récemment réessayé
        retry_tweets_iterator = bdd_direct_access.get_retry_tweets()
        
        # Prendre la date actuelle
        now = datetime.datetime.now()
        
        # Ressayer les Tweets échoués toutes les 24h
        retry_period = datetime.timedelta( hours = 24 )
        
        # File d'attente des Tweets à réessayer
        # Certains n'ont pas besoin d'être obtenu sur l'API
        tweets_queue = queue.Queue()
        
        # Liste des 100 premiers ID de Tweets à réessayer et qui n'ont pas
        # d'info dans la BDD (Ou moins)
        hundred_tweets = []
        
        # Parcourir les ID de Tweets à réessayer
        for tweet in retry_tweets_iterator :
            # Si le Tweet a été réessayé déjà 3 fois, il faut le supprimer
#            if tweet["retries_count"] > 3 :
#                bdd_direct_access.remove_retry_tweet( tweet["tweet_id"] )
#                continue
            # On ne supprime aucun tweet à réessayer, au cas où il y ait un
            # problème très embêtant, pour laisser le temps de réagir
            # Exemple : Coupure Internet, on ne gère pas cette erreur
            
            # Si le Tweet a été réessayé il y a moins de 24h
            if tweet["last_retry_date"] != None and now - tweet["last_retry_date"] < retry_period :
                # Si aucun Tweet n'est à réessayer, on dort
                if len( hundred_tweets ) == 0 and tweets_queue.qsize() == 0 :
                    # Reprise dans (retry_period - (now - tweet["last_retry_date"]))
                    wait_time = int( (retry_period - (now - tweet["last_retry_date"])).total_seconds() / 3 )
                    wait_time += 1 # Ajout de 3*1 = 3 secondes pour l'arrondi ci-dessus
                    
                    print( "[retry_failed_tweets_th" + str(thread_id) + "] Reprise dans " + str(wait_time*3) + " secondes, pour réessayer le Tweet ID " + str(tweet["tweet_id"]) + "." )
                    for i in range( wait_time ) :
                        sleep( 3 )
                        if not shared_memory.keep_service_alive :
                            break
                    # Recommencer la boucle du "keep_service_alive"
                    break # Arrête de l'itération "for"
            
            # Si il n'y a aucune info sur ce Tweet, il faut l'obtenir sur l'API
            # Ne devrait pas arriver, mais au cas où
            # Permet d'insérer manuellement des ID de Tweets dans la table
            if tweet["user_id"] == None :
                print( "[retry_failed_tweets_th" + str(thread_id) + "] Obtention et réindexation programés du Tweet ID : " + str(tweet["tweet_id"]) + " (Inséré manuellement)" )
                
                hundred_tweets.append( tweet["tweet_id"] )
                if len( hundred_tweets ) >= 100 :
                    break # Sortir du "while True"
            
            # Sinon, on peut l'ajouter directement à la file d'attente
            # Note : L'itérateur formate le dictionnaire de Tweet exactement
            # comme la fonction analyse_tweet_json()
            else :
                print( "[retry_failed_tweets_th" + str(thread_id) + "] Réindexation programée du Tweet ID : " + str(tweet["tweet_id"]) )
                tweets_queue.put( tweet )
        
        # Si il faut s'arrêter
        if not shared_memory.keep_service_alive : break
        
        # Si il n'y a pas de Tweet à réindexer
        if len( hundred_tweets ) == 0 and tweets_queue.qsize() == 0  :
            print( "[retry_failed_tweets_th" + str(thread_id) + "] Aucun Tweet à réessayer d'indexer !" )
            
            # Retest dans une heure (1200*3 = 3600)
            for i in range( 1200 ) :
                sleep( 3 )
                if not shared_memory.keep_service_alive :
                    break
            
            # Reboucler "while shared_memory.keep_service_alive"
            continue # Arrête de l'itération "for"
        
        # Si il y a des Tweets à aller chercher sur l'API
        if len( hundred_tweets ) > 0 :
            # Obtenir les JSON de tous les Tweets à réessayer
            # Ne figurent pas dans cette liste les Tweets qui ont étés supprimés
            response = twitter.api.statuses_lookup( hundred_tweets, trim_user = True, tweet_mode = "extended" )
            
            # Analyser les JSON et les mettre dans la file d'attente
            for tweet_json in response :
                tweets_queue.put( analyse_tweet_json( tweet_json._json ) )
            
        # Liste des tweets ayant ré-échoué
        refailed_tweets = []
        
        # Indexer les Tweets
        tweets_indexer.index_tweets( "", tweets_queue, FORCE_INDEX = True, FAILED_TWEETS_LIST = refailed_tweets )
        
        # Supprimer de la BDD les ID de Tweets à réessayer et dont le réessai
        # a réussi, ou qui n'étaient pas dans "response", c'est à dire qu'ils
        # ont étés supprimés
        for tweet_id in hundred_tweets :
            if not int(tweet_id) in refailed_tweets :
                bdd_direct_access.remove_retry_tweet( tweet_id )
    
    print( "[retry_failed_tweets_th" + str(thread_id) + "] Arrêté !" )
    return
