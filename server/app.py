#!/usr/bin/python3
# coding: utf-8

# Toujours la même erreur :
# [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)
# Ce fix est dangereux car désactive la vérication des certificats
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# On travaille dans le répertoire racine du serveur AOTF
# Toutes les importations se font depuis cet emplacement
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Protection pour le multiprocessing
if __name__ == "__main__" :
    """
    Script principal. NE PAS LE LANCER PLUSIEURS FOIS !
    """
    
    import threading
    import re
    
    try :
        import parameters as param
    except ModuleNotFoundError :
        print( "Fichier \"parameters.py\" introuvable !" )
        print( "Veuillez dupliquer \"parameters_sample.py\" vers \"parameters.py\", puis configurer ce-dernier." )
        import sys
        sys.exit(0)
    
    print( "Vérification des importations...")
    try :
        from app.check_parameters import check_parameters
        
        from app.error_collector import error_collector
        
        from app.thread_auto_update_accounts import thread_auto_update_accounts
        from app.thread_reset_SearchAPI_cursors import thread_reset_SearchAPI_cursors
        from app.thread_remove_finished_requests import thread_remove_finished_requests
        from app.thread_http_server import thread_http_server
        
        from app.user_pipeline.thread_step_1_link_finder import thread_step_1_link_finder
        from app.user_pipeline.thread_step_2_tweets_indexer import thread_step_2_tweets_indexer
        from app.user_pipeline.thread_step_3_reverse_search import thread_step_3_reverse_search
        from app.user_pipeline.thread_step_4_filter_results import thread_step_4_filter_results
        
        from app.scan_pipeline.thread_step_A_SearchAPI_list_account_tweets import thread_step_A_SearchAPI_list_account_tweets
        from app.scan_pipeline.thread_step_B_TimelineAPI_list_account_tweets import thread_step_B_TimelineAPI_list_account_tweets
        from app.scan_pipeline.thread_step_C_SearchAPI_index_account_tweets import thread_step_C_SearchAPI_index_account_tweets
        from app.scan_pipeline.thread_step_D_TimelineAPI_index_account_tweets import thread_step_D_TimelineAPI_index_account_tweets
        from app.scan_pipeline.thread_retry_failed_tweets import thread_retry_failed_tweets
        
        if param.ENABLE_MULTIPROCESSING :
            from shared_memory.thread_pyro_server import thread_pyro_server
        else :
            from shared_memory.class_Shared_Memory import Shared_Memory
    except ModuleNotFoundError as error :
        print( f"Il manque une librairie : {error}" )
        print( "Veuillez exécuter : pip install -r requirements.txt" )
        import sys
        sys.exit(0)
    else :
        print( "Toutes les librairies nécessaires sont présentes !" )
    
    
    """
    Vérification des paramètres.
    """
    if not check_parameters() :
        import sys
        sys.exit(0)
    
    """
    Augmentation du nombre maximum de descripteurs de fichiers.
    """
    try :
        import resource
    except ModuleNotFoundError : # On n'est pas sous un système UNIX
        pass
    else :
        # Augmenter le nombre de descripteurs de fichiers ouvrables.
        # 1024 par défaut, c'est trop peu pour nous !
        resource.setrlimit( resource.RLIMIT_NOFILE, (param.MAX_FILE_DESCRIPTORS, param.MAX_FILE_DESCRIPTORS) )
    print( f"Nombre maximum de descripteurs de fichiers : {param.MAX_FILE_DESCRIPTORS}" )
    
    """
    SI ON EST EN MULTIPROCESSING :
    Lancement du serveur de mémoire partagée, et accès pour ce processus (Le
    collecteur d'erreurs crée les accès pour les threads).
    """
    if param.ENABLE_MULTIPROCESSING :
        from random import randint
        
        # On démarre le serveur sur un port aléatoire, j'en ai marre des processus
        # fantomes qui massacrent tous mes tests !
        pyro_port = randint( 49152, 65535 )
        
        # Note : Je ne comprend pas bien pourquoi, mais sous Linux, en mode
        # multi-processus, les processus fils se connectent à leur frère
        # processus serveur Pyro, mais freezent sur "keep_service_alive", c'est
        # à dire à l'accès à un attribut. Idem sur ce processus père.
        # Du coup, on crée forcément le serveur Pyro en thread, ce qui n'est
        # pas génant puisque sur le processus pére (Ici, "app.py"), il n'y a
        # que la CLI.
        thread_pyro = threading.Thread( name = "thread_pyro_th1",
                                        target = thread_pyro_server,
                                        args = ( pyro_port, param.MAX_FILE_DESCRIPTORS, ) )
        thread_pyro.start()
        
        # On prépare la connexion au serveur.
        import Pyro4
        Pyro4.config.SERIALIZER = "pickle"
        shared_memory_uri = "PYRO:shared_memory@localhost:" + str(pyro_port)
        
        # On test pendant 30 secondes que la connection s'établisse.
        from time import sleep
        shared_memory = None
        for i in range( 30 ) :
            print( "Connexion au serveur de mémoire partagée..." )
            try :
                shared_memory = Pyro4.Proxy( shared_memory_uri )
                shared_memory.keep_service_alive # Test d'accès
            except ( Pyro4.errors.ConnectionClosedError, Pyro4.errors.CommunicationError, ConnectionRefusedError ) :
                sleep(1)
            else :
                print( "Connexion au serveur de mémoire partagée réussie !" )
                break
        
        if shared_memory == None :
            print( "Connexion au serveur de mémoire partagée impossible !" )
            import sys
            sys.exit(0)
    
    """
    SI ON N'EST PAS EN MULTIPROCESSING :
    Créer simplement l'objet de mémoire partagée.
    """
    if not param.ENABLE_MULTIPROCESSING :
        shared_memory = Shared_Memory( 0, 0 )
        shared_memory_uri = shared_memory # Pour passer aux threads
    
    """
    Garder des proxies ouverts.
    """
    shared_memory_user_requests = shared_memory.user_requests
    shared_memory_scan_requests = shared_memory.scan_requests
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_threads_registry = shared_memory.threads_registry
    
    # On s'enregistre comme thread / processus
    # ATTENTION : Pyro crée aussi pleins de threads (Mais pas des
    # processus comme nous en mode Multiprocessing) qui ne sont pas
    # enregistrés dans notre mémoire partagée.
    shared_memory_threads_registry.register_thread( "app.py", os.getpid() )
    
    
    """
    Démarrage des threads.
    Ce ne sont pas les procédures qui sont exécutées directement, mais le
    collecteur d'erreurs qui exécute la procédure.
    """
    if param.ENABLE_MULTIPROCESSING :
        import multiprocessing
        threading.Thread = multiprocessing.Process # Très bourrin, mais évite de faire plein de "if"
    
    # Liste contenant tous les threads
    threads = []
    
    for i in range( param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS ) :
        thread = threading.Thread( name = f"step_1_link_finder_th{i+1}",
                                   target = error_collector,
                                   args = ( thread_step_1_link_finder, i+1, shared_memory_uri, ) )
        thread.start()
        threads.append( thread )
    
    for i in range( param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS ) :
        thread = threading.Thread( name = f"step_2_tweets_indexer_th{i+1}",
                                   target = error_collector,
                                   args = ( thread_step_2_tweets_indexer, i+1, shared_memory_uri, ) )
        thread.start()
        threads.append( thread )
    
    for i in range( param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS ) :
        thread = threading.Thread( name = f"step_3_reverse_search_th{i+1}",
                                   target = error_collector,
                                   args = ( thread_step_3_reverse_search, i+1, shared_memory_uri, ) )
        thread.start()
        threads.append( thread )
    
    for i in range( param.NUMBER_OF_STEP_4_FILTER_RESULTS_THREADS ) :
        thread = threading.Thread( name = f"step_4_filter_results_th{i+1}",
                                   target = error_collector,
                                   args = ( thread_step_4_filter_results, i+1, shared_memory_uri, ) )
        thread.start()
        threads.append( thread )
    
    for i in range( param.NUMBER_OF_STEP_A_SEARCHAPI_LIST_ACCOUNT_TWEETS_THREADS ) :
        thread = threading.Thread( name = f"step_A_SearchAPI_list_account_tweets_th{i+1}",
                                   target = error_collector,
                                   args = ( thread_step_A_SearchAPI_list_account_tweets, i+1, shared_memory_uri, ) )
        thread.start()
        threads.append( thread )
    
    for i in range( param.NUMBER_OF_STEP_B_TIMELINEAPI_LIST_ACCOUNT_TWEETS_THREADS ) :
        thread = threading.Thread( name = f"step_B_TimelineAPI_list_account_tweets_th{i+1}",
                                   target = error_collector,
                                   args = ( thread_step_B_TimelineAPI_list_account_tweets, i+1, shared_memory_uri, ) )
        thread.start()
        threads.append( thread )
    
    for i in range( param.NUMBER_OF_STEP_C_SEARCHAPI_INDEX_ACCOUNT_TWEETS ) :
        thread = threading.Thread( name = f"step_C_SearchAPI_index_account_tweets_th{i+1}",
                                   target = error_collector,
                                   args = ( thread_step_C_SearchAPI_index_account_tweets, i+1, shared_memory_uri, ) )
        thread.start()
        threads.append( thread )
    
    for i in range( param.NUMBER_OF_STEP_D_TIMELINEAPI_INDEX_ACCOUNT_TWEETS ) :
        thread = threading.Thread( name = f"step_D_TimelineAPI_index_account_tweets_th{i+1}",
                                   target = error_collector,
                                   args = ( thread_step_D_TimelineAPI_index_account_tweets, i+1, shared_memory_uri, ) )
        thread.start()
        threads.append( thread )
    
    
    # On ne crée qu'un seul thread du serveur HTTP
    # C'est lui qui va créer plusieurs threads grace à la classe :
    # http.server.ThreadingHTTPServer()
    thread = threading.Thread( name = "http_server_th1",
                               target = error_collector,
                               args = ( thread_http_server, 1, shared_memory_uri, ) )
    thread.start()
    threads.append( thread )
    
    # On ne crée qu'un seul thread de mise à jour automatique
    thread = threading.Thread( name = "auto_update_accounts_th1",
                               target = error_collector,
                               args = ( thread_auto_update_accounts, 1, shared_memory_uri, ) )
    thread.start()
    threads.append( thread )
    
    # On ne crée qu'un seul thread de reset des curseurs d'indexation avec
    # l'API de recherche
    thread = threading.Thread( name = "thread_reset_SearchAPI_cursors_th1",
                               target = error_collector,
                               args = ( thread_reset_SearchAPI_cursors, 1, shared_memory_uri, ) )
    thread.start()
    threads.append( thread )
    
    # On ne crée qu'un seul thread de délestage de la liste des requêtes
    thread = threading.Thread( name = "remove_finished_requests_th1",
                               target = error_collector,
                               args = ( thread_remove_finished_requests, 1, shared_memory_uri, ) )
    thread.start()
    threads.append( thread )
    
    # On ne crée qu'un seul thread de retentative d'indexation de Tweets
    thread = threading.Thread( name = "thread_retry_failed_tweets_th1",
                               target = error_collector,
                               args = ( thread_retry_failed_tweets, 1, shared_memory_uri, ) )
    thread.start()
    threads.append( thread )
    
    
    """
    Entrée en ligne de commande (CLI).
    """
    # Initialisation de notre couche d'abstraction à l'API Twitter
    from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction
    twitter = TweepyAbstraction( param.API_KEY,
                                param.API_SECRET,
                                param.OAUTH_TOKEN,
                                param.OAUTH_TOKEN_SECRET )
    
    print( "Vous êtes en ligne de commande.")
    print( "Tapez `help` pour afficher l'aide.")
    
    if param.ENABLE_MULTIPROCESSING :
        print( "ATTENTION, serveur démarré en multiprocessing !" )
        print( "Il peut y avoir des problèmes d'affichage des messages et de processus fantômes, notamment sous Windows." )
        # En fait c'est parce qu'il faudrait flush stdout de temps en temps dans les sous-processus
        # Pour les processus fantômes, c'est quand on tue le processus père (Ou qu'il plante)
    
    if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
        print( "ATTENTION, vous utilisez SQLite. Pour de meilleure performances, il est très vivement conseillé d'utiliser MySQL !" )
    
    while True :
        command = input()
        args = command.split(" ")
        
        if args[0] == "request" :
            if len(args) == 2 :
                print( "Lancement de la procédure !" )
                shared_memory_user_requests.launch_request( args[1] )
            else :
                print( "Utilisation : request [URL de l'illustration]" )
        
        elif args[0] == "status" :
            if len(args) == 2 :
                request = shared_memory_user_requests.get_request( args[1] )
                if request != None :
                    print( f"Status : {request.status} {request.get_status_string()}" )
                    if request.problem != None :
                        print( f"Problème : {request.problem}" )
                    
                    if request.scan_requests == None :
                        print( "Cette requête n'a pas (encore ?) de requête de scan associée." )
                    elif request.scan_requests == [] :
                        print( "Cette requête n'a plus de requête de scan associée." )
                    else :
                        for scan_request_uri in request.scan_requests :
                            scan_request = Pyro4.Proxy( scan_request_uri )
                            print( f" - Scan @{scan_request.account_name} (ID {scan_request.account_id}), prioritaire : {scan_request.is_prioritary}" )
                            print( f"    - A démarré le listage SearchAPI : {scan_request.started_SearchAPI_listing}, TimelineAPI : {scan_request.started_SearchAPI_listing}" )
                            print( f"    - A terminé l'indexation SearchAPI : {scan_request.finished_SearchAPI_indexing}, TimelineAPI : {scan_request.finished_TimelineAPI_indexing}" )
                    
                    if request.finished_date != None :
                        print( f"Fin du traitement : {request.finished_date}" )
                else :
                    print( "Requête inconnue pour cet URL !" )
            else :
                print( "Utilisation : status [URL de l'illustration]" )
        
        elif args[0] == "result" :
            if len(args) == 2 :
                request = shared_memory_user_requests.get_request( args[1] )
                if request != None :
                    print( f"Comptes Twitter trouvés : {', '.join( [ f'@{account[0]} (ID {account[1]})' for account in request.twitter_accounts_with_id ] )}" )
                    print( f"Résultat : {[ (data.tweet_id, data.distance_chi2, data.distance_bhattacharyya ) for data in request.found_tweets ]}" )
                else :
                    print( "Requête inconnue pour cet URL !" )
            else :
                print( "Utilisation : result [URL de l'illustration]" )
        
        elif args[0] == "scan" :
            if len(args) == 2 :
                # Vérification que le nom d'utilisateur Twitter est possible
                if re.compile(r"^@?(\w){1,15}$").match(args[1]) :
                    account_name = args[1]
                    print( f"Demande de scan / d'indexation du compte @{account_name}." )
                    account_id = twitter.get_account_id( account_name )
                    
                    if account_id == None :
                        print( f"Compte @{args[1]} inexistant ou indisponible !" )
                    else :
                        shared_memory_scan_requests.launch_request( account_id, account_name )
                else :
                    print( "Nom de compte Twitter impossible !" )
            else :
                print( "Utilisation : scan [Nom du compte à scanner]" )
        
        elif args[0] == "search" :
            if len(args) in [ 2, 3 ] :
                if len(args) == 3 :
                    # Vérification que le nom d'utilisateur Twitter est possible
                    if re.compile(r"^@?(\w){1,15}$").match(args[2]) :
                        print( f"Recherche sur le compte @{args[2]}." )
                        account_id = twitter.get_account_id( args[2] )
                        
                        if account_id == None :
                            print( f"Compte @{args[2]} inexistant ou indisponible !" )
                        else :
                            print( "Attention ! Si ce compte n'est pas indexé, la recherche ne retournera aucun résultat." )
                            shared_memory_user_requests.launch_reverse_search_only( args[1], args[2], account_id )
                    else :
                        print( "Nom de compte Twitter impossible !" )
                else :
                    if shared_memory.tweets_count > 100000 :
                        print( "Il y a plus de 100 000 Tweets indexés dans votre base de données, la recherche prendrait trop de temps. Merci de préciser un compte Twitter sur lequel rechercher." )
                    else :
                        print( "Recherche dans toute la base de données !" )
                        shared_memory_user_requests.launch_reverse_search_only( args[1] )
            else :
                print( "Utilisation : search [URL de l'image à chercher] [Nom du compte Twitter (OPTIONNEL)]" )
        
        elif args[0] == "threads" :
            if len(args) == 1 :
                print( shared_memory_threads_registry.get_status() )
            else :
                print( "Utilisation : threads")
        
        elif args[0] == "queues" :
            if len(args) == 1 :
                to_print = f"Taille step_1_link_finder_queue : {shared_memory_user_requests.step_1_link_finder_queue.qsize()}\n"
                to_print += f"Taille step_2_tweets_indexer_queue : {shared_memory_user_requests.step_2_tweets_indexer_queue.qsize()}\n"
                to_print += f"Taille step_3_reverse_search_queue : {shared_memory_user_requests.step_3_reverse_search_queue.qsize()}\n"
                to_print += f"Taille step_4_filter_results_queue : {shared_memory_user_requests.step_4_filter_results_queue.qsize()}\n"
                to_print += f"Taille step_A_SearchAPI_list_account_tweets_prior_queue : {shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_prior_queue.qsize()}\n"
                to_print += f"Taille step_A_SearchAPI_list_account_tweets_queue : {shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_queue.qsize()}\n"
                to_print += f"Taille step_B_TimelineAPI_list_account_tweets_prior_queue : {shared_memory_scan_requests.step_B_TimelineAPI_list_account_tweets_prior_queue.qsize()}\n"
                to_print += f"Taille step_B_TimelineAPI_list_account_tweets_queue : {shared_memory_scan_requests.step_B_TimelineAPI_list_account_tweets_queue.qsize()}\n"
                to_print += f"Taille step_C_SearchAPI_index_account_tweets_prior_queue : {shared_memory_scan_requests.step_C_SearchAPI_index_account_tweets_prior_queue.qsize()}\n"
                to_print += f"Taille step_C_SearchAPI_index_account_tweets_queue : {shared_memory_scan_requests.step_C_SearchAPI_index_account_tweets_queue.qsize()}\n"
                to_print += f"Taille step_D_TimelineAPI_index_account_tweets_prior_queue : {shared_memory_scan_requests.step_D_TimelineAPI_index_account_tweets_prior_queue.qsize()}\n"
                to_print += f"Taille step_D_TimelineAPI_index_account_tweets_queue : {shared_memory_scan_requests.step_D_TimelineAPI_index_account_tweets_queue.qsize()}\n"
                to_print += f"Taille totale pipeline utilisateur : {shared_memory_user_requests.get_size()}\n"
                to_print += f"Taille totale pipeline de scan : {shared_memory_scan_requests.get_size()}"
                print( to_print )
            else :
                print( "Utilisation : queues")
        
        elif args[0] == "stats" :
            if len(args) == 1 :
                to_print = f"Nombre de tweets indexés : {shared_memory.tweets_count}\n"
                to_print += f"Nombre de comptes Twitter indexés : {shared_memory.accounts_count}\n"
                to_print += f"Nombre de requêtes dans le pipeline utilisateur : {shared_memory_user_requests.get_size()}\n"
                to_print += f"Nombre de requêtes dans le pipeline de scan : {shared_memory_scan_requests.get_size()}"
                print( to_print )
            else :
                print( "Utilisation : stats")
        
        elif args[0] == "metrics" :
            if len(args) == 1 :
                if not param.ENABLE_METRICS :
                    print( "Le paramètre \"ENABLE_METRICS\" est à \"False\" !" )
                else :
                    print( shared_memory_execution_metrics.get_metrics() )
            else :
                print( "Utilisation : metrics")
        
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
#    import requests
#    try :
#        requests.get( "http://localhost:" + str( param.HTTP_SERVER_PORT ) )
#    except requests.exceptions.ConnectionError :
#        pass
    # Edit : N'est plus bloquant car on lui a mis un timeout
    
    # Attendre que les threads aient fini
    for thread in threads :
        thread.join()
    
    if param.ENABLE_MULTIPROCESSING :
        shared_memory.keep_pyro_alive = False
        thread_pyro.join()
