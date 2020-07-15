#!/usr/bin/python3
# coding: utf-8

"""
Script principal. NE PAS LE LANCER PLUSIEURS FOIS !

Doit être utilisé avec IPython de préférance.
Sinon les messages des threads s'afficheront que lorsqu'il y aura une input.
"""

import threading
import re

from app import *
import parameters as param


# TODO : Thread de vidage de la liste des requêtes lorsqu'elles sont au niveau
# de traitement 8 (= Fin de traitement)


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
from tweet_finder.database import SQLite
# Accès direct à la base de données pour le processus principal
# N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
bdd_direct_access = SQLite( param.SQLITE_DATABASE_NAME )
def get_stats() :
    return bdd_direct_access.get_stats()


"""
Démarrage des threads.
"""
link_finder_threads = []
for i in range( param.NUMBER_OF_LINK_FINDER_THREADS ) :
    link_finder_thread = threading.Thread( name = "link_finder_" + str(i+1),
                                           target = link_finder_thread_main,
                                           args = ( i+1, pipeline, ) )
    link_finder_thread.start()
    link_finder_threads.append( link_finder_thread )

list_account_tweets_threads = []
for i in range( param.NUMBER_OF_LIST_ACCOUNT_TWEETS_THREADS ) :
    list_account_tweets_thread = threading.Thread( name = "list_account_tweets_" + str(i+1),
                                                     target = list_account_tweets_thread_main,
                                                     args = ( i+1, pipeline, ) )
    list_account_tweets_thread.start()
    list_account_tweets_threads.append( list_account_tweets_thread )

index_twitter_account_threads = []
for i in range( param.NUMBER_OF_INDEX_TWITTER_ACCOUNT_THREADS ) :
    index_twitter_account_thread = threading.Thread( name = "index_twitter_account_" + str(i+1),
                                                     target = index_twitter_account_thread_main,
                                                     args = ( i+1, pipeline, ) )
    index_twitter_account_thread.start()
    index_twitter_account_threads.append( index_twitter_account_thread )

reverse_search_threads = []
for i in range( param.NUMBER_OF_REVERSE_SEARCH_THREADS ) :
    reverse_search_thread = threading.Thread( name = "reverse_search_" + str(i+1),
                                              target = reverse_search_thread_main,
                                              args = ( i+1, pipeline, ) )
    reverse_search_thread.start()
    reverse_search_threads.append( reverse_search_thread )

http_server_threads = []
for i in range( param.NUMBER_OF_HTTP_SERVER_THREADS ) :
    http_server_thread = threading.Thread( name = "http_server_thread_" + str(i+1),
                                           target = http_server_thread_main,
                                           args = ( i+1, pipeline, ) )
    http_server_thread.start()
    http_server_threads.append( http_server_thread )


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
                
                # Fabrication de l'objet Request
                request = Request( None )
                request.twitter_accounts = [ args[1] ]
                
                # Lancement du scan
                pipeline.index_account_tweets_queue.put( request )
            else :
                print( "Nom de compte Twitter impossible !" )
        else :
            print( "Utilisation : scan [Nom du compte à scanner]" )
    
    elif args[0] == "search" :
        if len(args) in [ 2, 3 ] :
            # Fabrication de l'objet Request
            request = Request( args[1] )
            request.image_url = args[1]
            
            if len(args) == 3 :
                # Vérification que le nom d'utilisateur Twitter est possible
                if re.compile("^@?(\w){1,15}$").match(args[2]) :
                    print( "Recherche sur le compte @" + args[2] + "." )
                    request.twitter_accounts = [ args[2] ]
                    # Lancement de la recherche
                    pipeline.reverse_search_queue.put( request )
                else :
                    print( "Nom de compte Twitter impossible !" )
            else :
                print( "Recherche dans toute la base de données !" )
                # Lancement de la recherche
                pipeline.reverse_search_queue.put( request )
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
# Attendre que les threads aient fini
for thread in link_finder_threads :
    thread.join()
for thread in list_account_tweets_threads :
    thread.join()
for thread in index_twitter_account_threads :
    thread.join()
for thread in reverse_search_threads :
    thread.join()
for thread in http_server_threads :
    thread.join()
