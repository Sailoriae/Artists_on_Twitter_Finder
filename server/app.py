#!/usr/bin/python3
# coding: utf-8

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))


"""
Script principal. NE PAS LE LANCER PLUSIEURS FOIS !

Doit être utilisé avec IPython de préférance.
Sinon les messages des threads s'afficheront que lorsqu'il y aura une input.
"""

import threading
import re

from app import *
import parameters as param


"""
Vérification des paramètres.
"""
if not check_parameters() :
    import sys
    sys.exit(0)


"""
MEMOIRE PARTAGEE ENTRE LES THREADS.
Variable globale, partagées entre les threads.
Cet objet est passé en paramètre aux threads. Car en Python, les objets sont
passés par adresse.
"""
pipeline = Pipeline()


"""
Obtenir des statistiques sur la base de données.
Utilisé par la CLI.
@return Une liste contenant, dans l'ordre suivant :
        - Le nombre de tweets indexés,
        - Et nombre de comptes indexés.
"""
from tweet_finder.database import SQLite_or_MySQL
# Accès direct à la base de données pour le processus principal
# N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
bdd_direct_access = SQLite_or_MySQL()
def get_stats() :
    return bdd_direct_access.get_stats()


"""
Démarrage des threads.
Ce ne sont pas les procédures qui sont exécutées directement, mais le
collecteur d'erreurs qui exécute la procédure.
"""
threads_step_1_link_finder = []
for i in range( param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS ) :
    thread = threading.Thread( name = "step_1_link_finder_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_1_link_finder, i+1, pipeline, ) )
    thread.start()
    threads_step_1_link_finder.append( thread )

threads_step_2_GOT3_list_account_tweets = []
for i in range( param.NUMBER_OF_STEP_2_GOT3_LIST_ACCOUNT_TWEETS_THREADS ) :
    thread = threading.Thread( name = "step_2_GOT3_list_account_tweets_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_2_GOT3_list_account_tweets, i+1, pipeline, ) )
    thread.start()
    threads_step_2_GOT3_list_account_tweets.append( thread )

threads_step_3_GOT3_index_account_tweets = []
for i in range( param.NUMBER_OF_STEP_3_GOT3_INDEX_ACCOUNT_TWEETS ) :
    thread = threading.Thread( name = "step_3_GOT3_index_account_tweets_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_3_GOT3_index_account_tweets, i+1, pipeline, ) )
    thread.start()
    threads_step_3_GOT3_index_account_tweets.append( thread )

threads_step_4_TwitterAPI_index_account_tweets = []
for i in range( param.NUMBER_OF_STEP_4_TWITTERAPI_INDEX_ACCOUNT_TWEETS ) :
    thread = threading.Thread( name = "step_4_TwitterAPI_index_account_tweets_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_4_TwitterAPI_index_account_tweets, i+1, pipeline, ) )
    thread.start()
    threads_step_4_TwitterAPI_index_account_tweets.append( thread )

threads_step_5_reverse_search = []
for i in range( param.NUMBER_OF_STEP_5_REVERSE_SEARCH_THREADS ) :
    thread = threading.Thread( name = "step_5_reverse_search_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_5_reverse_search, i+1, pipeline, ) )
    thread.start()
    threads_step_5_reverse_search.append( thread )

# On ne crée qu'un seul thread du serveur HTTP
# C'est lui qui va créer plusieurs threads grace à la classe :
# http.server.ThreadingHTTPServer()
thread_http_server = threading.Thread( name = "http_server_th1",
                                       target = error_collector,
                                       args = ( thread_http_server, 1, pipeline, ) )
thread_http_server.start()

# On ne crée qu'un seul thread de mise à jour automatique
thread_auto_update_accounts = threading.Thread( name = "auto_update_accounts_th1",
                                                target = error_collector,
                                                args = ( thread_auto_update_accounts, 1, pipeline, ) )
thread_auto_update_accounts.start()

# On ne crée qu'un seul thread de délestage de la liste des requêtes
thread_remove_finished_requests = threading.Thread( name = "remove_finished_requests_th1",
                                                target = error_collector,
                                                args = ( thread_remove_finished_requests, 1, pipeline, ) )
thread_remove_finished_requests.start()


"""
Entrée en ligne de commande (CLI).
"""
print( "Vous êtes en ligne de commande.")
print( "Tapez `help` pour afficher l'aide.")

while True :
    command = input()
    args = command.split(" ")
    
    if args[0] == "request" :
        if len(args) == 2 :
            print( "Lancement de la procédure !" )
            pipeline.launch_full_process( args[1] )
        else :
            print( "Utilisation : request [URL de l'illustration]" )
    
    elif args[0] == "status" :
        if len(args) == 2 :
            request = pipeline.get_request( args[1] )
            if request != None :
                print( "Status : " + str(request.status) + " " + request.get_status_string() )
            else :
                print( "Requête inconnue pour cet URL !" )
        else :
            print( "Utilisation : status [URL de l'illustration]" )
    
    elif args[0] == "result" :
        if len(args) == 2 :
            request = pipeline.get_request( args[1] )
            if request != None :
                print( "Résultat : " + str( [ (data.tweet_id, data.distance) for data in request.founded_tweets ] ) )
            else :
                print( "Requête inconnue pour cet URL !" )
        else :
            print( "Utilisation : result [URL de l'illustration]" )
    
    elif args[0] == "scan" :
        if len(args) == 2 :
            # Vérification que le nom d'utilisateur Twitter est possible
            if re.compile("^@?(\w){1,15}$").match(args[1]) :
                print( "Demande de scan / d'indexation du compte @" + args[1] + "." )
                result = pipeline.launch_index_or_update_only( account_name = args[1] )
                
                if result == False :
                    print( "Compte @" + args[1] + " inexistant !" )
            else :
                print( "Nom de compte Twitter impossible !" )
        else :
            print( "Utilisation : scan [Nom du compte à scanner]" )
    
    elif args[0] == "search" :
        if len(args) in [ 2, 3 ] :
            # Fabrication de l'objet Request
            request = Request( None, pipeline, do_reverse_search = True )
            request.image_url = args[1]
            
            if len(args) == 3 :
                # Vérification que le nom d'utilisateur Twitter est possible
                if re.compile("^@?(\w){1,15}$").match(args[2]) :
                    print( "Recherche sur le compte @" + args[2] + "." )
                    request.twitter_accounts = [ args[2] ]
                    # Lancement de la recherche
                    pipeline.step_5_reverse_search_queue.put( request )
                else :
                    print( "Nom de compte Twitter impossible !" )
            else :
                print( "Recherche dans toute la base de données !" )
                # Lancement de la recherche
                pipeline.step_5_reverse_search_queue.put( request )
        else :
            print( "Utilisation : search [URL de l'image à chercher] [Nom du compte Twitter (OPTIONNEL)]" )
    
    elif args[0] == "stats" :
        if len(args) == 1 :
            stats = get_stats()
            print( "Nombre de tweets indexés : ", stats[0] )
            print( "Nombre de comptes Twitter indexés : ", stats[1] )
        else :
            print( "Utilisation : stats")
    
    elif args[0] == "stop" :
        if len(args) == 1 :
            print( "Arrêt à la fin des procédures en cours..." )
            pipeline.keep_service_alive = False
            break
        else :
            print( "Utilisation : stop")
    
    elif args[0] == "help" :
        if len(args) == 1 :
            print( "Lancer une requête : request [URL de l'illustration]\n" +
                   "Voir le status d'une requête : status [URL de l'illustration]\n" +
                   "Voir le résultat d'une requête : result [URL de l'illustration]\n" +
                   "\n" +
                   "Notes :\n" +
                   " - Une requête est une procédure complète pour un illustration\n" +
                   " - Les requêtes sont identifiées par l'URL de l'illustration.\n" +
                   "\n" +
                   "Forcer l'indexation de tous les tweets d'un compte : scan [Nom du compte à scanner]\n" +
                   "Rechercher une image dans la base de données : search [URL de l'image] [Nom du compte Twitter (OPTIONNEL)]\n" +
                   "\n" +
                   "Afficher des statistiques de la base de données : stats\n" +
                   "Arrêter le service : stop\n" +
                   "Afficher l'aide : help\n" )
        else :
            print( "Utilisation : help" )
    
    else :
        print( "Commande inconnue !" )


"""
Arrêt du système.
"""
# Même si keep_service_alice a été mis à False, il faut envoyer des requêtes au
# serveur HTTP pour qu'il sorte de sa boucle
# Car http_server.handle_request() est bloquant tant qu'il n'y a pas eu de
# requête
import requests
requests.get( "http://localhost:" + str( param.HTTP_SERVER_PORT ) )

# Attendre que les threads aient fini
for thread in threads_step_1_link_finder :
    thread.join()
for thread in threads_step_2_GOT3_list_account_tweets :
    thread.join()
for thread in threads_step_3_GOT3_index_account_tweets :
    thread.join()
for thread in threads_step_4_TwitterAPI_index_account_tweets :
    thread.join()
for thread in threads_step_5_reverse_search :
    thread.join()
thread_http_server.join()
thread_auto_update_accounts.join()
thread_remove_finished_requests.join()
