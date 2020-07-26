#!/usr/bin/python3
# coding: utf-8

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Problème étrange : Les tests de la classe CBIR_Engine_with_Database
# fonctionnent avec MySQL... Mais lorsqu'on démarre l'app complète, l'erreur
# suivant apparait au listage des Tweets par GOT3 : 
# <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
# unable to get local issuer certificate (_ssl.c:1108)>
# Très très étrange.
# Les lignes ci-dessous règles ces problèmes, mais désactivent la vérification
# SSL, ce qui est pas mal dangereux !
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


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
shared_memory = Shared_Memory()


"""
Démarrage des threads.
Ce ne sont pas les procédures qui sont exécutées directement, mais le
collecteur d'erreurs qui exécute la procédure.
"""
threads_step_1_link_finder = []
for i in range( param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS ) :
    thread = threading.Thread( name = "step_1_link_finder_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_1_link_finder, i+1, shared_memory, ) )
    thread.start()
    threads_step_1_link_finder.append( thread )

threads_step_2_tweets_indexer = []
for i in range( param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS ) :
    thread = threading.Thread( name = "step_2_tweets_indexer_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_2_tweets_indexer, i+1, shared_memory, ) )
    thread.start()
    threads_step_2_tweets_indexer.append( thread )

threads_step_3_reverse_search = []
for i in range( param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS ) :
    thread = threading.Thread( name = "step_3_reverse_search_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_3_reverse_search, i+1, shared_memory, ) )
    thread.start()
    threads_step_3_reverse_search.append( thread )

threads_step_A_GOT3_list_account_tweets = []
for i in range( param.NUMBER_OF_STEP_A_GOT3_LIST_ACCOUNT_TWEETS_THREADS ) :
    thread = threading.Thread( name = "step_A_GOT3_list_account_tweets_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_A_GOT3_list_account_tweets, i+1, shared_memory, ) )
    thread.start()
    threads_step_A_GOT3_list_account_tweets.append( thread )

threads_step_B_GOT3_index_account_tweets = []
for i in range( param.NUMBER_OF_STEP_B_GOT3_INDEX_ACCOUNT_TWEETS ) :
    thread = threading.Thread( name = "step_B_GOT3_index_account_tweets_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_B_GOT3_index_account_tweets, i+1, shared_memory, ) )
    thread.start()
    threads_step_B_GOT3_index_account_tweets.append( thread )

threads_step_C_TwitterAPI_index_account_tweets = []
for i in range( param.NUMBER_OF_STEP_C_TWITTERAPI_INDEX_ACCOUNT_TWEETS ) :
    thread = threading.Thread( name = "step_C_TwitterAPI_index_account_tweets_th" + str(i+1),
                               target = error_collector,
                               args = ( thread_step_C_TwitterAPI_index_account_tweets, i+1, shared_memory, ) )
    thread.start()
    threads_step_C_TwitterAPI_index_account_tweets.append( thread )

# On ne crée qu'un seul thread du serveur HTTP
# C'est lui qui va créer plusieurs threads grace à la classe :
# http.server.ThreadingHTTPServer()
thread_http_server = threading.Thread( name = "http_server_th1",
                                       target = error_collector,
                                       args = ( thread_http_server, 1, shared_memory, ) )
thread_http_server.start()

# On ne crée qu'un seul thread de mise à jour automatique
thread_auto_update_accounts = threading.Thread( name = "auto_update_accounts_th1",
                                                target = error_collector,
                                                args = ( thread_auto_update_accounts, 1, shared_memory, ) )
thread_auto_update_accounts.start()

# On ne crée qu'un seul thread de délestage de la liste des requêtes
thread_remove_finished_requests = threading.Thread( name = "remove_finished_requests_th1",
                                                target = error_collector,
                                                args = ( thread_remove_finished_requests, 1, shared_memory, ) )
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
            shared_memory.user_requests.launch_request( args[1] )
        else :
            print( "Utilisation : request [URL de l'illustration]" )
    
    elif args[0] == "status" :
        if len(args) == 2 :
            request = shared_memory.user_requests.get_request( args[1] )
            if request != None :
                print( "Status : " + str(request.status) + " " + request.get_status_string() )
            else :
                print( "Requête inconnue pour cet URL !" )
        else :
            print( "Utilisation : status [URL de l'illustration]" )
    
    elif args[0] == "result" :
        if len(args) == 2 :
            request = shared_memory.user_requests.get_request( args[1] )
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
                account_name = args[1]
                print( "Demande de scan / d'indexation du compte @" + account_name + "." )
                account_id = shared_memory.twitter.get_account_id( account_name )
                
                if account_id == None :
                    print( "Compte @" + args[1] + " inexistant ou indisponible !" )
                else :
                    shared_memory.scan_requests.launch_request( account_id, account_name )
            else :
                print( "Nom de compte Twitter impossible !" )
        else :
            print( "Utilisation : scan [Nom du compte à scanner]" )
    
    elif args[0] == "search" :
        if len(args) in [ 2, 3 ] :
            if len(args) == 3 :
                # Vérification que le nom d'utilisateur Twitter est possible
                if re.compile("^@?(\w){1,15}$").match(args[2]) :
                    print( "Recherche sur le compte @" + args[2] + "." )
                    print( "FONCTIONNALITE TEMPORAIREMENT INDISPONIBLE !" ) # TODO
                else :
                    print( "Nom de compte Twitter impossible !" )
            else :
                print( "Recherche dans toute la base de données !" )
                print( "FONCTIONNALITE TEMPORAIREMENT INDISPONIBLE !" ) # TODO
        else :
            print( "Utilisation : search [URL de l'image à chercher] [Nom du compte Twitter (OPTIONNEL)]" )
    
    elif args[0] == "threads" :
        if len(args) == 1 :
            to_print = ""
            for key in shared_memory.user_requests.requests_in_thread :
                value = shared_memory.user_requests.requests_in_thread[key]
                if value == None :
                    to_print += key + " : IDLE\n"
                else :
                    to_print += key + " : " + value.input_url + "\n"
            for key in shared_memory.scan_requests.requests_in_thread :
                value = shared_memory.scan_requests.requests_in_thread[key]
                if value == None :
                    to_print += key + " : IDLE\n"
                else :
                    to_print += key + " : @" + value.account_name + " (ID " + str(value.account_id) + ")\n"
            print( to_print )
        else :
            print( "Utilisation : threads")
    
    elif args[0] == "queues" :
        if len(args) == 1 :
            print( "step_1_link_finder_queue :", shared_memory.user_requests.step_1_link_finder_queue.qsize() )
            print( "step_2_tweets_indexer_queue :", shared_memory.user_requests.step_2_tweets_indexer_queue.qsize() )
            print( "step_3_reverse_search_queue :", shared_memory.user_requests.step_3_reverse_search_queue.qsize() )
            print( "step_A_GOT3_list_account_tweets_prior_queue :", shared_memory.scan_requests.step_A_GOT3_list_account_tweets_prior_queue.qsize() )
            print( "step_A_GOT3_list_account_tweets_queue :", shared_memory.scan_requests.step_A_GOT3_list_account_tweets_queue.qsize() )
            print( "step_B_GOT3_index_account_tweets_prior_queue :", shared_memory.scan_requests.step_B_GOT3_index_account_tweets_prior_queue.qsize() )
            print( "step_B_GOT3_index_account_tweets_queue :", shared_memory.scan_requests.step_B_GOT3_index_account_tweets_queue.qsize() )
            print( "step_C_TwitterAPI_index_account_tweets_prior_queue :", shared_memory.scan_requests.step_C_TwitterAPI_index_account_tweets_prior_queue.qsize() )
            print( "step_C_TwitterAPI_index_account_tweets_queue :", shared_memory.scan_requests.step_C_TwitterAPI_index_account_tweets_queue.qsize() )
        else :
            print( "Utilisation : queues")
    
    elif args[0] == "stats" :
        if len(args) == 1 :
            print( "Nombre de tweets indexés :", shared_memory.tweets_count )
            print( "Nombre de comptes Twitter indexés :", shared_memory.accounts_count )
        else :
            print( "Utilisation : stats")
    
    elif args[0] == "stop" :
        if len(args) == 1 :
            print( "Arrêt à la fin des procédures en cours..." )
            shared_memory.keep_service_alive = False
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
                   "Afficher ce que font les threads de traitement : threads\n" +
                   "Afficher la taille des files d'attente : queues\n" +
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
for thread in threads_step_2_tweets_indexer :
    thread.join()
for thread in threads_step_3_reverse_search :
    thread.join()
for thread in threads_step_A_GOT3_list_account_tweets :
    thread.join()
for thread in threads_step_B_GOT3_index_account_tweets :
    thread.join()
for thread in threads_step_C_TwitterAPI_index_account_tweets :
    thread.join()
thread_http_server.join()
thread_auto_update_accounts.join()
thread_remove_finished_requests.join()
