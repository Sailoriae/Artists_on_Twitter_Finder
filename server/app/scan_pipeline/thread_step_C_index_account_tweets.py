#!/usr/bin/python3
# coding: utf-8

import traceback

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
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL


"""
ETAPE C du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread d'indexation de n'importe quel Tweet trouvé par les méthodes de listage,
ou par les Tweets du thread de retentative d'indexation.
Traite la file d'attente suivante (Dans la mémoire partagée) :
shared_memory.scan_requests.step_C_SearchAPI_index_account_tweets_queue
"""
def thread_step_C_index_account_tweets( thread_id : int, shared_memory ) :
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_scan_requests = shared_memory.scan_requests
    
    # Fonction à passer à la classe "Tweets_Indexer"
    # Passer "shared_memory.keep_running" ne fonctionne pas
    def keep_running() : return shared_memory.keep_service_alive
    
    # Initialisation de l'indexeur de Tweets
    tweets_indexer = Tweets_Indexer(
        DEBUG = param.DEBUG,
        ENABLE_METRICS = param.ENABLE_METRICS,
        add_step_C_times = shared_memory_execution_metrics.add_step_C_times,
        keep_running = keep_running,
        end_request = shared_memory_scan_requests.end_request )
    
    # Fonction à passer à la méthode "Tweets_Indexer.index_tweets()"
    # Permet de sortir un Tweet de la file d'attente des Tweets à indexer.
    # Ceci se fait avec déclaration de manière sécurisé, voir la méthode
    # "Scan_Requests_Pipeline.get_tweet_to_index()".
    def tweets_queue_get() -> dict :
        return shared_memory_scan_requests.get_tweet_to_index( f"thread_step_C_index_account_tweets_th{thread_id}" )
    
    # Liste permettant d'enregistrer dans la BDD les Tweets sur lesquels
    # l'indexeur a éventuellement crashé
    current_tweet = []
    
    # Lancer l'indexeur, il travaille tout seul, et s'arrêtera tout seul
    try :
        tweets_indexer.index_tweets( tweets_queue_get,
                                     current_tweet = current_tweet )
    
    # On attrape les erreurs juste pour enregistrer le Tweet sur lequel on a
    # crashé. Il est important que le code ci-dessous soit très fail-safe, car
    # on est responsable de l'indexation, et donc il ne doit pas manquer un
    # seul Tweet.
    except Exception as error :
        tweet_is_safe = False
        scan_request_on_error = False
        if len(current_tweet) > 0 :
            tweet = current_tweet[0]
            if type(tweet) == dict :
                if "tweet_id" in tweet :
                    # On essaye de sauvegarder le Tweet dans la table "retry_tweets"
                    try :
                        account_id = None
                        image_1_url = None
                        image_2_url = None
                        image_3_url = None
                        image_4_url = None
                        if "user_id" in tweet :
                            account_id = tweet["user_id"]
                            if "images" in tweet :
                                length = len( tweet["images"] )
                                if length > 0 :
                                    image_1_url = tweet["images"][0]
                                if length > 1 :
                                    image_2_url = tweet["images"][1]
                                if length > 2 :
                                    image_3_url = tweet["images"][2]
                                if length > 3 :
                                    image_4_url = tweet["images"][3]
                        bdd = SQLite_or_MySQL()
                        bdd.add_retry_tweet(
                            tweet["tweet_id"],
                            account_id,
                            image_1_url,
                            image_2_url,
                            image_3_url,
                            image_4_url,
                        )
                        tweet_is_safe = True
                    except Exception :
                        file = open( "thread_step_C_index_account_tweets_errors.log", "a" )
                        file.write( f"Erreur avec le Tweet ID {tweet['tweet_id']} !\n" )
                        file.write( "Il y a eu un problème lors de la tentative d'enregistrer le Tweet dans la table des Tweets à réessayer d'indexer.")
                        file.write( "Il est recommandé d'insérer manuellement l'ID du Tweet dans la table \"retry_tweets\" !" )
                        file.write( "Traceback du problème :" )
                        traceback.print_exc( file = file )
                        file.write( "\n\n\n" )
                        file.close()
                    
                    # On essaye aussi de mettre la requête de scan associée en erreur
                    try :
                        if "user_id" in tweet :
                            account_id = tweet["user_id"]
                            request = shared_memory_scan_requests.get_request( int(account_id) )
                            if request != None :
                                request.has_failed = True
                                scan_request_on_error = True
                    except Exception :
                        file = open( "thread_step_C_index_account_tweets_errors.log", "a" )
                        file.write( f"Erreur avec le Tweet ID {tweet['tweet_id']} !\n" )
                        file.write( "Il y a eu un problème lors de la tentative de mettre la requête de scan associée en échec.")
                        file.write( "Il est recommandé d'insérer manuellement l'ID du Tweet dans la table \"retry_tweets\" !" )
                        file.write( "Traceback du problème :" )
                        traceback.print_exc( file = file )
                        file.write( "\n\n\n" )
                        file.close()
        
        # On passe au collecteur d'erreurs
        message = "Erreur dans un thread d'indexation !"
        message += "\nListe \"current_tweet\" : " + str(current_tweet)
        if scan_request_on_error :
            message += "\nLa requête de scan associée a été trouvée et mise en échec."
        if tweet_is_safe :
            message += "\nLe Tweet en cours d'indexation a été récupéré et ajouté à la table \"reindex_tweets\"."
        elif len(current_tweet) > 0 :
            message += "\nLe Tweet en cours d'indexation n'a pas pu être sauvé dans la table \"reindex_tweets\" !"
            message += "\nMerci de vérifier vous même la liste \"current_tweet\" afin d'ajouter manuellement l'ID du Tweet à la table \"reindex_tweets\"."
            message += "\nVous pouvez aussi plus simplement mettre à \"NULL\" les curseurs d'indexation pour l'ID du compte Twitter."
        else :
            message += "\nAucun Tweet en cours d'indexation."
        raise Exception( message ) from error
    
    print( f"[step_C_th{thread_id}] Arrêté !" )
    return
