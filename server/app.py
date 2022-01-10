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
    import signal
    import sys
    
    
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
        from app.class_Command_Line_Interface import Command_Line_Interface
        
        from shared_memory.launch_shared_memory import launch_shared_memory
        from threads.launch_threads import launch_threads
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
    Lancement de la mémoire partagée.
    En mode multi-processus, ceci lance le thread du serveur Pyro.
    """
    shared_memory, thread_pyro = launch_shared_memory( MAX_FILE_DESCRIPTORS )
    
    # Si échec du lancement du serveur de mémoire partagée.
    if shared_memory == None :
        if param.DEBUG : close_debug()
        sys.exit(0)
    
    # On s'enregistre comme thread / processus.
    # Note : Pyro crée aussi pleins de threads (Mais pas des processus comme
    # nous en mode multi-processus) qui ne sont pas enregistrés dans notre
    # registre des threads. Et ce n'est pas grave.
    shared_memory.threads_registry.register_thread( "app.py", os.getpid() )
    
    
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
    threads_or_process = launch_threads( shared_memory.get_URI() )
    
    
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
    Retourne uniquement si la commande "stop" est éxécutée.
    """
    cli = Command_Line_Interface( shared_memory )
    cli.do_cli_loop()
    
    
    """
    Arrêt du système (Si commande "stop").
    """
    wait_and_stop()
