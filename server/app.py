#!/usr/bin/python3
# coding: utf-8

"""
SCRIPT PRINCIPAL DU SERVEUR "ARTISTS ON TWITTER FINDER".
NE PAS LE LANCER PLUSIEURS FOIS ! En cas de plusieurs lancement, le script
détectera que le port de son serveur HTTP est indisponible, et donc refusera
de se lancer.

Ce script est la racine du serveur AOTF. Il réalise les opérations suivantes :
- Vérification de l'existence du fichier "parameters.py"
- Importation de tout le serveur, ce qui permet de vérifier que les librairies
  sont installées
- Lancement de la fonction de vérification des paramètres, qui permet notamment
  de vérifier leurs types, et si ils sont utilisables (API Twitter et MySQL)
- Création de la mémoire partagée, c'est à dire lancement du serveur Pyro si on
  est en mode multi-processus, ou sinon création de l'objet "Shared_Memory"
- Lancement des threads ou processus.
- Exécution de la boucle infinie de la ligne de commande (back-end, et donc
  attente d'une commande.
  Si le serveur reçoit la commande "stop", ou reçoit un signal "SIGTERM", il
  arrête cette boucle infinie, et demande l'arrêt des threads et/ou processus.
- Attente de l'arrêt des threads et/ou processus.
- Demande et attente de l'arrêt du serveur Pyro (Si mode multi-processus.
"""

# Toujours la même erreur :
# [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1123)
# Ce fix est dangereux car désactive la vérication des certificats
#import ssl
#ssl._create_default_https_context = ssl._create_unverified_context

# On travaille dans le répertoire racine du serveur AOTF
# Toutes les importations se font depuis cet emplacement
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# On écrase la fonction "print()" par défaut de Python. On peut vérifier
# facilement que ceci s'appliquer récursivement à tous les modules importés, et
# dans tous les threads et processus fils.
import builtins
builtin_print = print
def custom_print ( *args, **kwargs ) :
    try :
        # Ligne de test pour vérifier que cette fonction soit bien appelée.
#        builtin_print( "[TEST]", *args, **kwargs )
        # On force le vidage du buffer de sortie à chaque appel.
        builtin_print( *args, **kwargs, flush = True )
    # On gère le cas où STDOUT est fermé. Cela arrive notamment lorsqu'on
    # reçoit un signal SIGHUP (Voir la gestion de ce signal plus bas).
    except OSError as error :
        if error.errno == 5 : pass # I/O error
        else : raise error
builtins.print = custom_print

# Protection pour le multiprocessing
if __name__ == "__main__" :
    import threading
    import re
    import signal
    import sys
    
    # Il suffit juste d'importer ce module pour avoir un historique des entrées
    # dans "input()", ce qui permet d'avoir un historique de la CLI.
    # Note : Ce module n'est pas disponible sous Windows ou MacOS, il faut
    # installer la libairie PyReadline.
    try :
        import readline # readline ou pyreadline
    except ModuleNotFoundError :
        print( "Il est recommandé d'installer la librairie PyReadline afin d'avoir un historique des commandes éxécutées dans la CLI du serveur AOTF, rendant ainsi son utilisation plus pratique." )
        print( "Pour se faire, éxécutez la commande suivante :\npip install pyreadline")
    
    """
    Par mesure de sécurité, on empêche l'éxécution en tant que "root".
    """
    if hasattr( os, "geteuid" ) : # Sinon, c'est qu'on est sous Windows
        if os.geteuid() == 0 : # UID de "root" = 0
            print( "Ce script ne peut pas être éxécuté en tant que super-utilisateur." )
            print( "Ceci est un principe de sécurité." )
            sys.exit(0)
    
    
    """
    En cas de Ctrl+C ou de SIGTERM lors de la phase d'initilisation.
    On remplacera cette gestion après l'initialisation (Voir plus bas).
    """
    def on_sigterm ( signum, frame ) :
        print( "Démarrage annulé." )
        sys.exit(0)
    
    signal.signal(signal.SIGINT, on_sigterm)
    signal.signal(signal.SIGTERM, on_sigterm)
    
    
    """
    Vérification de l'existence du fichier des paramètres.
    """
    try :
        import parameters as param
    except ModuleNotFoundError :
        print( "Fichier \"parameters.py\" introuvable !" )
        print( "Veuillez dupliquer \"parameters_sample.py\" vers \"parameters.py\", puis configurer ce-dernier." )
        sys.exit(0)
    
    
    """
    Importation des modules du serveur AOTF, ce qui permet de vérifier que
    les librairies Python nécessaires sont installées.
    """
    print( "Vérification des importations...")
    try :
        from app.check_parameters import check_parameters
        
        from app.threads_launchers import launch_thread, launch_identical_threads_in_container, launch_unique_threads_in_container
        
        from app.thread_auto_update_accounts import thread_auto_update_accounts
        from app.thread_reset_SearchAPI_cursors import thread_reset_SearchAPI_cursors
        from app.thread_remove_finished_requests import thread_remove_finished_requests
        from app.thread_http_server import thread_http_server
        
        from app.user_pipeline.thread_step_1_link_finder import thread_step_1_link_finder
        from app.user_pipeline.thread_step_2_tweets_indexer import thread_step_2_tweets_indexer
        from app.user_pipeline.thread_step_3_reverse_search import thread_step_3_reverse_search
        
        from app.scan_pipeline.thread_step_A_SearchAPI_list_account_tweets import thread_step_A_SearchAPI_list_account_tweets
        from app.scan_pipeline.thread_step_B_TimelineAPI_list_account_tweets import thread_step_B_TimelineAPI_list_account_tweets
        from app.scan_pipeline.thread_step_C_index_account_tweets import thread_step_C_index_account_tweets
        from app.scan_pipeline.thread_retry_failed_tweets import thread_retry_failed_tweets
        
        if param.ENABLE_MULTIPROCESSING :
            from shared_memory.thread_pyro_server import thread_pyro_server
        else :
            from shared_memory.class_Shared_Memory import Shared_Memory
        from shared_memory.open_proxy import open_proxy
    except ModuleNotFoundError as error :
        # Si c'est une vraie ModuleNotFoundError, elle contient le nom du module
        if error.name != None and error.name != "" :
            print( f"Il manque la librairie suivante : {error.name}" )
            print( "Veuillez exécuter : pip install -r requirements.txt" )
        # Sinon, c'est nous qui l'avons créée, et donc elle a un message propre
        else :
            print( "Il y a eu un problème lors de la vérification des librairies." )
            print( error )
        sys.exit(0)
    else :
        print( "Toutes les librairies nécessaires sont présentes !" )
    
    
    """
    Vérification des paramètres.
    """
    if not check_parameters() :
        sys.exit(0)
    
    
    """
    Augmentation du nombre maximum de descripteurs de fichiers.
    1024 par défaut, c'est trop peu pour nous ! Car chaque connexion au serveur
    de mémoire partagée est un nouveau descripteur de fichier.
    """
    # Threads de traitement (Etapes 1, 2, 3, A, B et C)
    MAX_FILE_DESCRIPTORS = 0
    MAX_FILE_DESCRIPTORS += 300 * param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS
    MAX_FILE_DESCRIPTORS += 300 * param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS
    MAX_FILE_DESCRIPTORS += 300 * param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS
    MAX_FILE_DESCRIPTORS += 300 * len( param.TWITTER_API_KEYS ) # Nombre de threads de listage avec l'API de recherche (Etape A)
    MAX_FILE_DESCRIPTORS += 300 * len( param.TWITTER_API_KEYS ) # Nombre de threads de listage avec l'API de timeline (Etape B)
    MAX_FILE_DESCRIPTORS += 300 * param.NUMBER_OF_STEP_C_INDEX_ACCOUNT_TWEETS
    
    # Serveur HTTP et autres, même si on a déjà une bonne marge
    MAX_FILE_DESCRIPTORS += 2000
    
    try :
        import resource
    except ModuleNotFoundError : # On n'est pas sous un système UNIX
        pass
    else :
        resource.setrlimit( resource.RLIMIT_NOFILE, (MAX_FILE_DESCRIPTORS, MAX_FILE_DESCRIPTORS) )
        print( f"Nombre maximum de descripteurs de fichiers : {MAX_FILE_DESCRIPTORS}" )
    
    
    """
    Ouverture du fichier de débug. Penser à le fermer !
    Celui-ci est avec un buffer de ligne (Vidé à chaque "\n").
    """
    if param.DEBUG :
        debug_file = open( "debug.log", "a", buffering = 1 )
        def write_debug ( line ) :
            try : debug_file.write( line + "\n" )
            except Exception : pass # Mesure de sécurité
        def close_debug () :
            try : debug_file.close()
            except Exception : pass # Mesure de sécurité
        write_debug( "[app.py] Fichier de débug ouvert." )
    
    
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
        # processus serveur Pyro, mais freezent sur "keep_threads_alive", c'est
        # à dire à l'accès à un attribut. Idem sur ce processus père.
        # Du coup, on crée forcément le serveur Pyro en thread, ce qui n'est
        # pas génant puisque sur le processus pére (Ici, "app.py"), il n'y a
        # que la CLI.
        thread_pyro = threading.Thread( name = "thread_pyro_th1",
                                        target = thread_pyro_server,
                                        args = ( pyro_port, MAX_FILE_DESCRIPTORS, ) )
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
                shared_memory = open_proxy( shared_memory_uri )
                shared_memory.keep_threads_alive # Test d'accès
            except ( Pyro4.errors.ConnectionClosedError, Pyro4.errors.CommunicationError, ConnectionRefusedError ) :
                sleep(1)
            else :
                print( "Connexion au serveur de mémoire partagée réussie !" )
                break
        
        if shared_memory == None :
            print( "Connexion au serveur de mémoire partagée impossible !" )
            if param.DEBUG :
                close_debug()
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
    Démarrage des threads ou processus.
    Ce ne sont pas les procédures qui sont exécutées directement, mais le
    collecteur d'erreurs qui exécute la procédure.
    
    IMPORTANT : Si on est en Multiprocessing, aucun thread ne doit être créé
    directement en tant que fils de "app.py", car il y a déjà le serveur Pyro.
    Les procédures qui peuvent rester des threads afin d'économiser de la RAM
    doivent être éxécutés dans un processus conteneur.
    
    Voir le fichier "threads_launchers.py"...
    """
    print( f"Démarrage des {'processus et threads' if param.ENABLE_MULTIPROCESSING else 'threads'}." )
    if param.DEBUG :
        write_debug( f"[app.py] Démarrage des {'processus et threads' if param.ENABLE_MULTIPROCESSING else 'threads'}." )
    
    # Liste contenant tous les threads ou processus
    threads_or_process = []
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_1_link_finder,
        param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS,
        False, # Ne nécessitent pas des processus séparés (Seront placés dans un processus conteneur sui on est en Multiprocessing)
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_2_tweets_indexer,
        param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS,
        False, # Ne nécessitent pas des processus séparés
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_3_reverse_search,
        param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS,
        True, # Nécessitent des processus séparés (Car il font de la recherche de vecteurs similaires)
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_A_SearchAPI_list_account_tweets,
        len( param.TWITTER_API_KEYS ), # Il doit y avoir autant de threads de listage que de clés d'API dans TWITTER_API_KEYS
        False, # Ne nécessitent pas des processus séparés
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_B_TimelineAPI_list_account_tweets,
        len( param.TWITTER_API_KEYS ), # Il doit y avoir autant de threads de listage que de clés d'API dans TWITTER_API_KEYS
        False, # Ne nécessitent pas des processus séparés
        shared_memory_uri ) )
    
    threads_or_process.extend( launch_identical_threads_in_container(
        thread_step_C_index_account_tweets,
        param.NUMBER_OF_STEP_C_INDEX_ACCOUNT_TWEETS,
        True, # Nécessitent des processus séparés (Car ils font de l'indexation, donc de l'analyse d'images)
        shared_memory_uri ) )
    
    
    # On ne crée qu'un seul thread (ou processus) du serveur HTTP
    # C'est lui qui va créer plusieurs threads grace à la classe :
    # http.server.ThreadingHTTPServer()
    threads_or_process.append( launch_thread(
        thread_http_server,
        1, True, # Nécessite un processus séparé
        shared_memory_uri ) )
    
    
    # Liste des procédures de maintenance
    # Elles ne nécessitent pas d'être dans des processus séparés
    # Et elles doivent être uniques
    maintenance_procedures = []
    maintenance_procedures.append( thread_auto_update_accounts ) # Mise à jour automatique
    maintenance_procedures.append( thread_reset_SearchAPI_cursors ) # Reset des curseurs d'indexation avec l'API de recherche
    maintenance_procedures.append( thread_remove_finished_requests ) # Délestage de la liste des requêtes
    maintenance_procedures.append( thread_retry_failed_tweets ) # Retentative d'indexation de Tweets
    
    # Lancer les procédures de maintenance
    threads_or_process.extend( launch_unique_threads_in_container(
        maintenance_procedures,
        False, # Ne nécessitent pas des processus séparés
        "thread_maintenance", # Respecte la convention de nommage
        shared_memory_uri ) )
    
    
    """
    Fonction d'arrêt du serveur AOTF.
    Peut être utilisée lors de la fin de la CLI (Commande "stop"), ou lors d'un
    SIGTERM (Ce qui empêche la sortie du "input()", problème avec le module
    Python "readline" qui ne fait rien en cas d'EOF).
    
    Cette fonction attend que les threads se terminent, puis arrête la mémoire
    partagée (Pyro) si on est en multiprocessus.
    """
    wait_and_stop_once = threading.Semaphore()
    def wait_and_stop () :
        if not wait_and_stop_once.acquire( blocking = False ) :
            return # Déjà en cours
        
        if param.DEBUG :
            write_debug( "[app.py] Arrêt initié." )
        
        try : print( "Arrêt à la fin des procédures en cours..." )
        except OSError : pass # Par mesure de sécurité
        
        shared_memory.keep_threads_alive = False
        for thread in threads_or_process :
            thread.join()
        if param.ENABLE_MULTIPROCESSING :
            shared_memory.keep_pyro_alive = False
            thread_pyro.join()
        
        if param.DEBUG :
            write_debug( "[app.py] Arrêt terminé." )
            close_debug()
        
        try :
            sys.exit(0)
        except SystemExit :
            os._exit(0) # Forcer
    
    
    """
    Ecouter les signaux nous demandant de nous arrêter.
    On le fait après avoir démarré les processus fils, car ils créent eux aussi
    leurs fonctions d'écoute, qui envoient des "SIGTERM" à leur père, c'est à
    dire ici. Voir le fichier "threads_launchers.py".
    """
    def on_sigterm ( signum, frame ) :
        if param.DEBUG :
            write_debug( f"[app.py] Signal {signal.Signals(signum).name} reçu." )
        
        wait_and_stop()
    
    signal.signal(signal.SIGINT, on_sigterm)
    signal.signal(signal.SIGTERM, on_sigterm)
    
    # Lorsque une "screen" reçoit un SIGTERM, elle envoie à son fils un signal
    # SIGHUP. Cela inclue aussi que STDOUT et STDIN sont fermés. Il faut donc
    # avertir nos processus fils pour qu'ils restaurent leur STDOUT, puis on
    # restaure le notre, afin de ne pas crasher sur un print().
    def on_sighup ( signum, frame ) :
        if param.DEBUG :
            write_debug( f"[app.py] Signal {signal.Signals(signum).name} reçu." )
        
        if param.ENABLE_MULTIPROCESSING :
            # Il n'y a que des objets "Process" dans la liste "threads".
            for process in threads_or_process :
                os.kill(process.pid, signal.SIGHUP)
        sys.stdout = open( os.devnull, "w" )
        
        wait_and_stop() # Arrêter le serveur
    
    try : signal.signal(signal.SIGHUP, on_sighup)
    except AttributeError : pass # Windows
    
    
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
        
        # Ajout : Si on éxécute AOTF avec CMD sous Windows ou Bash sous Linux, les messages s'affichent très bien
        # En revanche, MINGW64 empêche l'affichage des messages depuis les threads (Buffer ne se vide pas ?)
        # Liste de solutions possibles : https://stackoverflow.com/a/35467658
        # Note : Désactiver complètement le buffer (python -u) est une mauvaise idée, car les messages peuvent s'entremêler
    
    if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
        print( "ATTENTION, vous utilisez SQLite. Pour de meilleure performances, il est très vivement conseillé d'utiliser MySQL !" )
    
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
                request = shared_memory_user_requests.launch_request( args[1] )
                
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
            else :
                print( "Utilisation : query [URL de l'illustration]" )
        
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
                request = None
                
                if len(args) == 3 :
                    # Vérification que le nom d'utilisateur Twitter est possible
                    if re.compile(r"^@?(\w){1,15}$").match(args[2]) :
                        print( f"Recherche sur le compte @{args[2]}." )
                        print( "Attention : Si ce compte n'existe pas ou n'est pas indexé, la recherche ne retournera aucun résultat." )
                        request = shared_memory_user_requests.launch_direct_request( args[1], args[2] )
                    else :
                        print( "Nom de compte Twitter impossible !" )
                else :
                    print( "Recherche dans toute la base de données !" )
                    print( "ATTENTION : Pour des raisons de performances, seules les images de Tweets ayant exactement la même empreinte seront retournées. Cela mène à un peu moins de 10% de faux-négatifs !" )
                    request = shared_memory_user_requests.launch_direct_request( args[1] )
                
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
            else :
                print( "Utilisation : search [URL de l'image à chercher] [Nom du compte Twitter (OPTIONNEL)]" )
        
        elif args[0] == "threads" :
            if len(args) == 1 :
                print( shared_memory_threads_registry.get_status() )
            else :
                print( "Utilisation : threads")
        
        elif args[0] == "queues" :
            if len(args) == 1 :
                to_print = f"Taille step_1_link_finder_queue : {shared_memory_user_requests.step_1_link_finder_queue.qsize()} requêtes\n"
                to_print += f"Taille step_2_tweets_indexer_queue : {shared_memory_user_requests.step_2_tweets_indexer_queue.qsize()} requêtes\n"
                to_print += f"Taille step_3_reverse_search_queue : {shared_memory_user_requests.step_3_reverse_search_queue.qsize()} requêtes\n"
                to_print += f"Taille step_A_SearchAPI_list_account_tweets_prior_queue : {shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_prior_queue.qsize()} requêtes\n"
                to_print += f"Taille step_A_SearchAPI_list_account_tweets_queue : {shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_queue.qsize()} requêtes\n"
                to_print += f"Taille step_B_TimelineAPI_list_account_tweets_prior_queue : {shared_memory_scan_requests.step_B_TimelineAPI_list_account_tweets_prior_queue.qsize()} requêtes\n"
                to_print += f"Taille step_B_TimelineAPI_list_account_tweets_queue : {shared_memory_scan_requests.step_B_TimelineAPI_list_account_tweets_queue.qsize()} requêtes\n"
                to_print += f"Taille step_C_index_account_tweets_queue : {shared_memory_scan_requests.step_C_index_account_tweets_queue.qsize()} Tweets\n"
                to_print += f"Nombre de requêtes utilisateur en cours de traitement : {shared_memory_user_requests.processing_requests_count} requêtes\n"
                to_print += f"Nombre de requêtes de scan en cours de traitement : {shared_memory_scan_requests.processing_requests_count} requêtes"
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
                break # Appel de "wait_and_stop()" après la boucle de la CLI
            else :
                print( "Utilisation : stop")
        
        elif args[0] == "help" :
            if len(args) == 1 :
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
                       f"Afficher les {'processus et threads' if param.ENABLE_MULTIPROCESSING else 'threads'} et ce qu'ils font : threads\n" +
                       "Afficher la taille des files d'attente : queues\n" +
                       "Arrêter le serveur : stop\n" +
                       "Afficher l'aide : help" )
            else :
                print( "Utilisation : help" )
        
        else :
            print( "Commande inconnue !" )
    
    
    """
    Arrêt du système.
    """
    wait_and_stop()
