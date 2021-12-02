#!/usr/bin/python3
# coding: utf-8

from time import time
import datetime

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
from tweet_finder.analyse_tweet_json import analyse_tweet_json
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
from app.wait_until import wait_until


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Thread qui retente d'indexer les Tweets dont l'indexation d'une image au moins
a échoué, c'est à dire que la méthode suivante a retourné "None" :
Tweets_Indexer.get_image_hash()

C'est l'étape C qui se charge de l'indexation, et si elle réussie, de supprimer
le Tweet de la table des Tweets à réessayer.
"""
def thread_retry_failed_tweets( thread_id : int, shared_memory ) :
    # Sécurité, vérifier que le thread est unique
    if thread_id != 1 :
        raise AssertionError( "Ce thread doit être unique, et doit pas conséquent avoir 1 comme identifiant (\"thread_id\") !" )
    
    # Accès direct à la base de données
    bdd = SQLite_or_MySQL()
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    # Ne devrait pas être utilisée en temps normal
    # Mais permet d'insérer manuellement des ID de Tweets dans la table "reindex_tweets"
    twitter = TweepyAbstraction( param.API_KEY,
                                 param.API_SECRET,
                                 param.OAUTH_TOKEN,
                                 param.OAUTH_TOKEN_SECRET )
    
    # Ressayer les Tweets échoués toutes les 6h
    retry_period = datetime.timedelta( hours = 6 )
    
    # Passer le maximum de Tweets dans une requête
    rate_limit_period = datetime.timedelta( minutes = 15 )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    step_C_index_account_tweets_queue = shared_memory.scan_requests.step_C_index_account_tweets_queue
    
    # Fonction à passer à "wait_until()"
    # Passer "shared_memory.keep_running" ne fonctionne pas
    def break_wait() : return not shared_memory.keep_threads_alive
    
    # Historique des ID de Tweets dont on a lancé le réessai
    # ID du Tweet -> Nombre de réessai
    # Permet de ne pas mettre deux fois le Tweet dans la file de l'étape C
    # (Se produit si jamais elle est très remplie)
    retried_tweets = {}
    
    # Liste des ID de Tweets qu'on rencontre durant l'itération, permet à la
    # fin de nettoyer le dictionnaire "retried_tweets"
    retried_tweets_ids = []
    
    # Obtenir et lancer la réindexation de Tweets dont on n'a pas les infos
    def get_and_retry_tweets( hundred_tweets ) :
        # Obtenir les JSON de tous les Tweets à réessayer
        # Ne figurent pas dans cette liste les Tweets qui ont
        # étés supprimés
        response = twitter.get_multiple_tweets( hundred_tweets, trim_user = True )
        
        # Analyser les JSON et les mettre dans la file d'attente
        for tweet_json in response :
            tweet = analyse_tweet_json( tweet_json._json )
            if tweet == None :
                # C'est possible que Twitter perdent des images et que les
                # Tweets n'aient plus d'image associée
                print( f"[retry_failed_tweets_th{thread_id}] Le Tweet ID {tweet_json._json['id_str']} n'a pas d'image associée." )
                continue
            print( f"[retry_failed_tweets_th{thread_id}] Demande de réindexation du Tweet ID {tweet['tweet_id']} envoyée !" )
            tweet["was_failed_tweet"] = True
            tweet["force_index"] = True
            step_C_index_account_tweets_queue.put( tweet )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_threads_alive :
        # Prendre l'itérateur sur les Tweets à réessayer, triés dans l'ordre du
        # moins récemment réessayé au plus récemment réessayé
        retry_tweets_iterator = bdd.get_retry_tweets()
        
        # Prendre la date actuelle
        now = datetime.datetime.now()
        start = datetime.datetime.now()
        
        # Liste des 100 premiers ID de Tweets à réessayer et qui n'ont pas
        # d'info dans la BDD (Ou moins)
        hundred_tweets = []
        
        # Parcourir les ID de Tweets à réessayer
        for tweet in retry_tweets_iterator :
            # Si le Tweet a été réessayé déjà 3 fois, il faut le supprimer
#            if tweet["retries_count"] > 3 :
#                bdd.remove_retry_tweet( tweet["tweet_id"] )
#                continue
            # On ne supprime aucun tweet à réessayer, au cas où il y ait un
            # problème très embêtant, pour laisser le temps de réagir
            # Exemple : Coupure Internet, on ne gère pas cette erreur
            
            # Noter qu'on a rencontré ce Tweet, sert au nettoyage du
            # dictionnaire "retried_tweets"
            retried_tweets_ids.append( int( tweet["tweet_id"] ) )
            
            # Si on a rencontré ce Tweet lors de la denière itération et que
            # son nombre de réessais est le même, c'est qu'il est encore dans
            # la file de l'étape C, on le laisse donc tranquille
            if int( tweet["tweet_id"] ) in retried_tweets :
                if retried_tweets[ int( tweet["tweet_id"] ) ] == tweet["retries_count"] :
                    continue
            retried_tweets[ int( tweet["tweet_id"] ) ] = tweet["retries_count"]
            
            # Si le Tweet a été réessayé il y a moins de "retry_period"
            if tweet["last_retry_date"] != None and now - tweet["last_retry_date"] < retry_period :
                # Si le Tweet est à réessayer dans plus de 15 minutes (Période
                # des rate limits), ou que la liste "hundred_tweets" est vide,
                # on peut dormir
                if now - tweet["last_retry_date"] > rate_limit_period or len( hundred_tweets ) == 0:
                    # Mais avant, si il y a des Tweets dans la liste
                    # "hundred_tweets", il faut les traiter
                    if len( hundred_tweets ) > 0 :
                        get_and_retry_tweets( hundred_tweets )
                        hundred_tweets = []
                    
                    # Reprise dans (retry_period - (now - tweet["last_retry_date"]))
                    wait_time = int( (retry_period - (now - tweet["last_retry_date"])).total_seconds() )
                    end_sleep_time = time() + wait_time
                    
                    print( f"[retry_failed_tweets_th{thread_id}] Reprise dans {wait_time} secondes, pour réessayer le Tweet ID {tweet['tweet_id']}." )
                    
                    if not wait_until( end_sleep_time, break_wait ) :
                        break # Arrêt de l'itération "for"
                    
                    # MàJ la date actuelle
                    now = datetime.datetime.now()
                
                # Sinon, c'est pas grave qu'on prenne 15 minutes d'avance, le
                # but est de passer le plus de Tweets possible dans la liste
                # "hundred_tweets"
            
            # Si il n'y a aucune info sur ce Tweet, il faut l'obtenir sur l'API
            # Ne devrait pas arriver, mais au cas où
            # Permet d'insérer manuellement des ID de Tweets dans la table
            if tweet["user_id"] == None :
                print( f"[retry_failed_tweets_th{thread_id}] Obtention du Tweet ID {tweet['tweet_id']} (Inséré manuellement) programmée !" )
                
                hundred_tweets.append( tweet["tweet_id"] )
                if len( hundred_tweets ) >= 100 :
                    get_and_retry_tweets( hundred_tweets )
                    hundred_tweets = []
            
            # Sinon, on peut l'ajouter directement à la file d'attente
            # Note : L'itérateur formate le dictionnaire de Tweet exactement
            # comme la fonction analyse_tweet_json()
            else :
                print( f"[retry_failed_tweets_th{thread_id}] Demande de réindexation du Tweet ID {tweet['tweet_id']} envoyée !" )
                tweet["was_failed_tweet"] = True
                tweet["force_index"] = True
                step_C_index_account_tweets_queue.put( tweet )
        
        # Vérifier que l'itération "for" n'est pas était arrêtée pour éteindre
        # le serveur
        if not shared_memory.keep_threads_alive : break
        
        # Si il y a des Tweets dans "hundred_tweets", il faut les traiter
        if len( hundred_tweets ) > 0 :
            get_and_retry_tweets( hundred_tweets )
            hundred_tweets = []
        
        # Sortir du dictionnaire "retried_tweets" les Tweets qui ne sont plus
        # dans la table "reindex_tweets", c'est à dure qu'on n'a pas vu dans
        # l'itérateur précédent
        for tweet_id in retried_tweets :
            if not tweet_id in retried_tweets_ids :
                del retried_tweets[tweet_id]
        
        # Calculer le temps restant de la période de réessai
        # Car tous les Tweets qu'AOTF ajoute dans la table "reindex_tweets"
        # sont datés et donc devront être réessayés après
        wait_time = int( (retry_period - (datetime.datetime.now() - start)).total_seconds() )
        end_sleep_time = time() + wait_time
        if len( retried_tweets_ids ) == 0 :
            print( f"[retry_failed_tweets_th{thread_id}] Aucun Tweet à réessayer d'indexer, reprise dans {int(wait_time)} secondes." )
        else :
            print( f"[retry_failed_tweets_th{thread_id}] Fin du parcours des Tweets à réessayer d'indexer, reprise dans {int(wait_time)} secondes." )
        
        # Vider la liste "retried_tweets_ids"
        retried_tweets_ids.clear()
        
        # On dort le temps restant de la période de réessai
        if not wait_until( end_sleep_time, break_wait ) :
            break # Le serveur doit s'arrêter
    
    print( f"[retry_failed_tweets_th{thread_id}] Arrêté !" )
    return
