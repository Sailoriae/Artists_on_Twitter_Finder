#!/usr/bin/python3
# coding: utf-8

from time import time
import datetime
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
    change_wdir( "../.." )
    path.append(get_wdir())

import parameters as param
from tweet_finder.class_Tweets_Indexer import Tweets_Indexer
from tweet_finder.analyse_tweet_json import analyse_tweet_json
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
from app.wait_until import wait_until


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Thread qui retente d'indexer les Tweets dont l'indexation d'une image au moins
a échoué, c'est à dire que la méthode suivante a retourné "None" :
Tweets_Indexer.get_image_hash()
"""
def thread_retry_failed_tweets( thread_id : int, shared_memory ) :
    # Sécurité, vérifier que le thread est unique
    if thread_id != 1 :
        raise RuntimeError( "Ce thread doit être unique, et doit pas conséquent avoir 1 comme identifiant (\"thread_id\") !" )
    
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
    
    # Ressayer les Tweets échoués toutes les 6h
    retry_period = datetime.timedelta( hours = 6 )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    step_C_index_account_tweets_queue = shared_memory.scan_requests.step_C_index_account_tweets_queue
    
    # Fonction à passer à "wait_until()"
    # Passer "shared_memory.keep_running" ne fonctionne pas
    def break_wait() : return not shared_memory.keep_service_alive
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        # Prendre l'itérateur sur les Tweets à réessayer, triés dans l'ordre du
        # moins récemment réessayé au plus récemment réessayé
        retry_tweets_iterator = bdd_direct_access.get_retry_tweets()
        
        # Prendre la date actuelle
        now = datetime.datetime.now()
        
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
            
            # Si le Tweet a été réessayé il y a moins de "retry_period"
            if tweet["last_retry_date"] != None and now - tweet["last_retry_date"] < retry_period :
                # Si aucun Tweet n'est à réessayer, on dort
                if len( hundred_tweets ) == 0 :
                    # Reprise dans (retry_period - (now - tweet["last_retry_date"]))
                    wait_time = int( (retry_period - (now - tweet["last_retry_date"])).total_seconds() )
                    end_sleep_time = time() + wait_time
                    
                    print( f"[retry_failed_tweets_th{thread_id}] Reprise dans {wait_time} secondes, pour réessayer le Tweet ID {tweet['tweet_id']}." )
                    
                    if not wait_until( end_sleep_time, break_wait ) :
                        break # Arrêt de l'itération "for"
                    
                    # MàJ la date actuelle
                    now = datetime.datetime.now()
                
                # Sinon, on arrête l'itération "for" pour indexer les Tweets
                # qu'on a déjà à réessayer
                else :
                   break
            
            # Si il n'y a aucune info sur ce Tweet, il faut l'obtenir sur l'API
            # Ne devrait pas arriver, mais au cas où
            # Permet d'insérer manuellement des ID de Tweets dans la table
            if tweet["user_id"] == None :
                print( f"[retry_failed_tweets_th{thread_id}] Obtention et réindexation du Tweet ID {tweet['tweet_id']} (Inséré manuellement)." )
                
                hundred_tweets.append( tweet["tweet_id"] )
                if len( hundred_tweets ) >= 100 :
                    break # Sortir du "while True"
            
            # Sinon, on peut l'ajouter directement à la file d'attente
            # Note : L'itérateur formate le dictionnaire de Tweet exactement
            # comme la fonction analyse_tweet_json()
            else :
                print( f"[retry_failed_tweets_th{thread_id}] Demande de réindexation du Tweet ID {tweet['tweet_id']} envoyée !" )
                tweet["was_failed_tweet"] = True
                tweet["force_index"] = True
                step_C_index_account_tweets_queue.put( tweet )
        
        # Si il faut s'arrêter
        if not shared_memory.keep_service_alive : break
        
        # Si il n'y a pas de Tweet à réindexer
        if len( hundred_tweets ) == 0  :
            print( f"[retry_failed_tweets_th{thread_id}] Aucun Tweet à réessayer d'indexer !" )
            
            # Retest dans une heure = 3600 secondes
            end_sleep_time = time() + 3600
            if not wait_until( end_sleep_time, break_wait ) :
                break # Le serveur doit s'arrêter
            
            # Reboucler "while shared_memory.keep_service_alive"
            continue
        
        # Si il y a des Tweets à aller chercher sur l'API
        else :
            # Obtenir les JSON de tous les Tweets à réessayer
            # Ne figurent pas dans cette liste les Tweets qui ont étés supprimés
            response = twitter.api.statuses_lookup( hundred_tweets, trim_user = True, tweet_mode = "extended" )
            
            # Analyser les JSON et les mettre dans la file d'attente
            for tweet_json in response :
                print( f"[retry_failed_tweets_th{thread_id}] Demande de réindexation du Tweet ID {tweet['tweet_id']} envoyée !" )
                tweet = analyse_tweet_json( tweet_json._json )
                tweet["was_failed_tweet"] = True
                tweet["force_index"] = True
                step_C_index_account_tweets_queue.put( tweet )
    
    print( f"[retry_failed_tweets_th{thread_id}] Arrêté !" )
    return
