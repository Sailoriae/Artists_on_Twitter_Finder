#!/usr/bin/python3
# coding: utf-8

import sys
import re
import traceback
from datetime import datetime
from time import sleep

# Il suffit juste d'importer ce module pour avoir un historique des entrées
# dans "input()", ce qui permet d'avoir un historique de la CLI.
# Note : Ce module n'est pas disponible sous Windows ou MacOS, il faut
# installer la libairie PyReadline.
try :
    import readline # readline ou pyreadline
except ModuleNotFoundError :
    print( "Il est recommandé d'installer la librairie PyReadline afin d'avoir un historique des commandes exécutées dans la CLI du serveur AOTF, rendant ainsi son utilisation plus pratique." )
    print( "Pour se faire, exécutez la commande suivante :\npip install pyreadline")

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
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

import parameters as param
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
from shared_memory.open_proxy import open_proxy


"""
Classe de la l'entrée en ligne de commande (CLI) pour le back-end.
"""
class Command_Line_Interface :
    """
    Constructeur.
    """
    def __init__ ( self, shared_memory, threads_manager ) :
        self._shared_memory = shared_memory
        self._threads_manager = threads_manager
        
        # Garder des proxies ouverts
        self._shared_memory_user_requests = shared_memory.user_requests
        self._shared_memory_scan_requests = shared_memory.scan_requests
        self._shared_memory_execution_metrics = shared_memory.execution_metrics
        self._shared_memory_threads_registry = shared_memory.threads_registry
        
        # Connexion à l'API Twitter (Pour certaines commandes)
        self._twitter = TweepyAbstraction( param.API_KEY,
                                           param.API_SECRET,
                                           param.OAUTH_TOKEN,
                                           param.OAUTH_TOKEN_SECRET )
    
    """
    Collecteur d'erreurs à l'entrée en ligne de commande. Si "app.py" plante,
    ça devient compliqué d'arrêter le serveur.
    """
    def do_cli_loop ( self ) :
        print( "Vous êtes en ligne de commande.")
        print( "Tapez `help` pour afficher l'aide.")
        
        while True :
            try :
                self._do_cli_loop()
            except Exception as error :
                # Si c'est que STDIN est fermé, on peut quitter
                if sys.stdin.closed :
                    print( "STDIN fermé ! Arrêt de la ligne de commande." )
                    break
                
                error_name = "Erreur dans l'entrée en ligne de commande !\n"
                error_name +=  f"S'est produite le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.\n"
                
                file = open( "method_Command_Line_Interface.do_cli_loop_errors.log", "a" )
                file.write( "ICI LE COLLECTEUR D'ERREURS DE LA LIGNE DE COMMANDE !\n" )
                file.write( "Je suis dans le fichier suivant : app/class_Command_Line_Interface.py\n" )
                file.write( error_name )
                traceback.print_exc( file = file )
                file.write( "\n\n\n" )
                file.close()
                
                print( error_name, end = "" )
                print( f"{type(error).__name__}: {error}" )
                print( "La pile d'appel complète a été écrite dans un fichier." )
                
                # Eviter de trop reboucler
                sleep( 1 )
            else :
                break
    
    """
    Boucle infinie de l'entrée en ligne de commande.
    Elle peut être arrêtée de trois manières différentes :
    - Soit en exécutant la commande "stop".
    - Soit en envoyant un EOF dans STDIN.
    - Soit en exéccutant "sys.exit()".
    """
    def _do_cli_loop ( self ) :
        while True :
            try :
                command = input()
                
            # Sert aussi lors d'un SIGHUP, car fermeture de STDIN.
            except EOFError :
                print( "EOF reçu ! Arrêt de la ligne de commande." )
                break
            
            args = command.split(" ")
            
            if args[0] == "query" :
                if len(args) == 2 :
                    self._do_query( args[1] )
                else :
                    print( "Utilisation : query [URL de l'illustration]" )
            
            elif args[0] == "scan" :
                if len(args) == 2 :
                    self._do_scan( args[1] )
                else :
                    print( "Utilisation : scan [Nom du compte à scanner]" )
            
            elif args[0] == "search" :
                if len(args) == 2 :
                    self._do_search( args[1] )
                elif len(args) == 3 :
                    self._do_search( args[1], args[2] )
                else :
                    print( "Utilisation : search [URL de l'image à chercher] [Nom du compte Twitter (OPTIONNEL)]" )
            
            elif args[0] == "threads" :
                if len(args) == 1 :
                    self._do_threads()
                else :
                    print( "Utilisation : threads")
            
            elif args[0] == "queues" :
                if len(args) == 1 :
                    self._do_queues()
                else :
                    print( "Utilisation : queues")
            
            elif args[0] == "stats" :
                if len(args) == 1 :
                    self._do_stats()
                else :
                    print( "Utilisation : stats")
            
            elif args[0] == "metrics" :
                if len(args) == 1 :
                    self._do_metrics()
                else :
                    print( "Utilisation : metrics")
            
            elif args[0] == "stacks" :
                if len(args) == 1 :
                    self._do_stacks()
                else :
                    print( "Utilisation : stacks")
            
            elif args[0] == "help" :
                if len(args) == 1 :
                    self._do_help()
                else :
                    print( "Utilisation : help")
            
            elif args[0] == "stop" :
                if len(args) == 1 :
                    break # Sortir de la boucle infinie de la LI
                else :
                    print( "Utilisation : stop")
            
            else :
                print( "Commande inconnue !" )
    
    """
    Commande "query" : Permet de lancer et de voir le résultat d'une requête
    utilisateur. Fonctionne comme l'api "/query".
    """
    def _do_query ( self, illust_url ) :
        request = self._shared_memory_user_requests.launch_request( illust_url )
        
        print( f"Status : {request.status} {request.get_status_string()}" )
        if request.problem != None :
            print( f"Problème : {request.problem}" )
        
        if request.scan_requests == None :
            if request.status < 3 : # Si n'est pas encore passée au moins une fois dans l'étape 2
                print( "Cette requête n'a pas (encore ?) de requête de scan associée." )
            else :
                print( "Cette requête n'a pas de requête de scan associée." )
        elif request.scan_requests == [] :
            print( "Cette requête n'a plus de requête de scan associée." )
        else :
            for scan_request_uri in request.scan_requests :
                scan_request = open_proxy( scan_request_uri )
                print( f" - Scan @{scan_request.account_name} (ID {scan_request.account_id}), prioritaire : {'OUI' if scan_request.is_prioritary else 'NON'}" )
                print( f"    - A démarré le listage SearchAPI : {'OUI' if scan_request.started_SearchAPI_listing else 'NON'}, TimelineAPI : {'OUI' if scan_request.started_TimelineAPI_listing else 'NON'}" )
                print( f"    - A terminé l'indexation SearchAPI : {'OUI' if scan_request.finished_SearchAPI_indexing else 'NON'}, TimelineAPI : {'OUI' if scan_request.finished_TimelineAPI_indexing else 'NON'}" )
        
        if request.finished_date != None :
            print( f"Fin du traitement : {request.finished_date}" )
        
        if request.status > 1 : # Si a dépassé le Link Finder (Etape 1)
            if len( request.twitter_accounts_with_id ) > 0 :
                s = f"{'s' if len( request.twitter_accounts_with_id ) > 1 else ''}"
                print( f"Compte{s} Twitter trouvé{s} : {', '.join( [ f'@{account[0]} (ID {account[1]})' for account in request.twitter_accounts_with_id ] )}" )
            else :
                print( "Aucun compte Twitter trouvé !" )
        
        if request.status == 6 : # Si a dépassé la recherche inverée (Etape 3)
            if len( request.found_tweets ) > 0 :
                s = f"{'s' if len( request.found_tweets ) > 1 else ''}"
                print( f"Tweet{s} trouvé{s} : {', '.join( [ f'ID {tweet.tweet_id} (Distance {tweet.distance})' for tweet in request.found_tweets ] )}" )
            else :
                print( "Aucun Tweet trouvé !" )
            
    
    """
    Commande "scan" : Permet de lancer l'indexation ou la mise à jour de
    l'index d'un compte Twitter.
    """
    def _do_scan ( self, account_name ) :
        # Vérification que le nom d'utilisateur Twitter est possible
        if re.compile( r"^@?(\w){1,15}$" ).match( account_name ) :
            account_id = self._twitter.get_account_id( account_name )
            
            if account_id == None :
                print( f"Compte @{account_name} inexistant ou indisponible !" )
            else :
                print( f"Demande de scan / d'indexation du compte @{account_name}." )
                self._shared_memory_scan_requests.launch_request( account_id, account_name )
        else :
            print( "Nom de compte Twitter impossible !" )
            
    
    """
    Commande "search" : Permet de lancer et de voir le résultat une recherche
    d'image dans toute la base de données, ou sur un compte en particulier.
    """
    def _do_search ( self, image_url, account_name = None ) :
        request = None
        
        # Note : Ne pas être tenté d'aller vérifier l'ID du compte Twitter.
        # Parce que du coup il sera validé à chaque requête, ou alors il faut
        # faire un cache, donc un truc complexe en plus. Il y a des erreurs
        # dans les requêtes directes qui sont adaptées. Ca ne sert à rien
        # d'ajouter une vérification ici.
        if account_name != None :
            # Vérification que le nom d'utilisateur Twitter est possible
            if re.compile( r"^@?(\w){1,15}$" ).match( account_name ) :
                print( f"Recherche sur le compte @{account_name}." )
                print( "Attention : Si ce compte n'existe pas ou n'est pas indexé, la recherche ne retournera aucun résultat." )
                request = self._shared_memory_user_requests.launch_direct_request( image_url, account_name )
            else :
                print( "Nom de compte Twitter impossible !" )
        else :
            print( "Recherche dans toute la base de données !" )
            print( "ATTENTION : Pour des raisons de performances, seules les images de Tweets ayant exactement la même empreinte seront retournées. Cela mène à un peu moins de 10% de faux-négatifs !" )
            request = self._shared_memory_user_requests.launch_direct_request( image_url )
        
        # Affichage très similaire à celui de la commande "query"
        if request != None :
            print( f"Status : {request.status} {request.get_status_string()}" )
            if request.problem != None :
                print( f"Problème : {request.problem}" )
            
            if request.finished_date != None :
                print( f"Fin du traitement : {request.finished_date}" )
            
            if request.status == 6 : # Si a dépassé la recherche inverée (Etape 3)
                if len( request.found_tweets ) > 0 :
                    s = f"{'s' if len( request.found_tweets ) > 1 else ''}"
                    print( f"Tweet{s} trouvé{s} : {', '.join( [ f'ID {tweet.tweet_id} (Distance {tweet.distance})' for tweet in request.found_tweets ] )}" )
                else :
                    print( "Aucun Tweet trouvé !" )
    
    """
    Commande "threads" : Permet d'afficher les threads en cours d'exécution,
    ainsi que ce qu'ils sont en trainde faire.
    """
    def _do_threads ( self ) :
        print( self._shared_memory_threads_registry.get_status() )
    
    """
    Commande "queues" : Permet d'afficher la taille des files d'attentes des
    différentes threads de traitement.
    """
    def _do_queues ( self ) :
        to_print = f"Taille step_1_link_finder_queue : {self._shared_memory_user_requests.step_1_link_finder_queue.qsize()} requêtes\n"
        to_print += f"Taille step_2_tweets_indexer_queue : {self._shared_memory_user_requests.step_2_tweets_indexer_queue.qsize()} requêtes\n"
        to_print += f"Taille step_3_reverse_search_queue : {self._shared_memory_user_requests.step_3_reverse_search_queue.qsize()} requêtes\n"
        to_print += f"Taille step_A_SearchAPI_list_account_tweets_prior_queue : {self._shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_prior_queue.qsize()} requêtes\n"
        to_print += f"Taille step_A_SearchAPI_list_account_tweets_queue : {self._shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_queue.qsize()} requêtes\n"
        to_print += f"Taille step_B_TimelineAPI_list_account_tweets_prior_queue : {self._shared_memory_scan_requests.step_B_TimelineAPI_list_account_tweets_prior_queue.qsize()} requêtes\n"
        to_print += f"Taille step_B_TimelineAPI_list_account_tweets_queue : {self._shared_memory_scan_requests.step_B_TimelineAPI_list_account_tweets_queue.qsize()} requêtes\n"
        to_print += f"Taille step_C_index_tweets_queue : {self._shared_memory_scan_requests.step_C_index_tweets_queue.qsize()} Tweets\n"
        to_print += f"Nombre de requêtes utilisateur en cours de traitement : {self._shared_memory_user_requests.processing_requests_count} requêtes\n"
        to_print += f"Nombre de requêtes de scan en cours de traitement : {self._shared_memory_scan_requests.processing_requests_count} requêtes"
        print( to_print )
    
    """
    Commande "stats" : Permet d'afficher des statistiques sur la base de
    données et la taille des pipelines de traitement.
    """
    def _do_stats ( self ) :
        to_print = f"Nombre de tweets indexés : {self._shared_memory.tweets_count}\n"
        to_print += f"Nombre de comptes Twitter indexés : {self._shared_memory.accounts_count}\n"
        to_print += f"Nombre de requêtes dans le pipeline utilisateur : {self._shared_memory_user_requests.get_size()}\n"
        to_print += f"Nombre de requêtes dans le pipeline de scan : {self._shared_memory_scan_requests.get_size()}"
        print( to_print )
    
    """
    Commande "metrics" : Permet d'afficher les moyennes des temps d'exécutions
    mesurés à différents endroits du serveur.
    """
    def _do_metrics ( self ) :
        if not param.ENABLE_METRICS :
            print( "Le paramètre \"ENABLE_METRICS\" est à \"False\" !" )
        else :
            print( self._shared_memory_execution_metrics.get_metrics() )
    
    """
    Commande "metrics" : Permet d'écrire les piles d'appels des threads dans un
    fichier. En mode multi-processus, cela envoie un ordre aux processus fils.
    """
    def _do_stacks ( self ) :
        print( "Ecriture des piles d'appels des threads." )
        self._threads_manager.write_stacks()
    
    """
    Commande "help" : Permet d'afficher l'aide sur les commandes de la CLI.
    """
    def _do_help ( self ) :
        print( "Lancer une requête et voir son état : query [URL de l'illustration]\n" +
               "Relancez cette commande pour voir l'avancement de la requête.\n" +
               "\n" +
               "Notes :\n" +
               " - Une requête est une procédure complète pour une illustration.\n" +
               " - Les requêtes sont identifiées par l'URL de l'illustration.\n" +
               "\n" +
               "Indexer ou mettre à jour l'indexation des Tweets d'un compte : scan [Nom du compte à scanner]\n" +
               "Rechercher une image dans la base de données : search [URL de l'image] [Nom du compte Twitter (OPTIONNEL)]\n" +
               "Relancez cette commande pour voir l'avancement de la requête.\n" +
               "\n" +
               "Afficher des statistiques de la base de données : stats\n" +
               f"Afficher les threads et ce qu'ils font : threads\n" +
               "Afficher la taille des files d'attente : queues\n" +
               "Afficher les mesures de temps d'exécution : metrics\n" +
               "Ecrire les piles d'appels dans un fichier : stacks\n" +
               "Arrêter le serveur : stop\n" +
               "Afficher l'aide : help" )
