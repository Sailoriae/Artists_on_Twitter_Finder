#!/usr/bin/python3
# coding: utf-8

"""
SCRIPT PRINCIPAL DU SERVEUR "ARTISTS ON TWITTER FINDER".
NE PAS LE LANCER PLUSIEURS FOIS ! En cas de plusieurs lancement, le script
détectera que le port de son serveur HTTP est indisponible, et donc refusera
de se lancer.

Ce script est la racine du serveur AOTF. Il réalise les opérations suivantes :
- Vérification de l'existence du fichier "parameters.py".
- Importation de tout le serveur, ce qui permet de vérifier que les librairies
  sont installées.
- Lancement de la fonction de vérification des paramètres, qui permet notamment
  de vérifier leurs types, et si ils sont utilisables (API Twitter et MySQL)
- Instantiation du gestionnaire de threads
- Création de la mémoire partagée, c'est à dire lancement du serveur Pyro si on
  est en mode multi-processus, ou sinon création de l'objet "Shared_Memory".
- Lancement des threads et processus si on est en multi-processus.
- Exécution de la boucle infinie de la ligne de commande (back-end), et donc
  attente d'une commande.
  Si le serveur reçoit la commande "stop", ou reçoit un signal "SIGTERM", il
  arrête cette boucle infinie, et demande l'arrêt des threads et/ou processus.
- Attente de l'arrêt des threads et processus.
- Demande et attente de l'arrêt du serveur Pyro (Si mode multi-processus).
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
    # Importations de librairies standards de Python.
    import sys
    
    # Par mesure de sécurité, on empêche l'exécution en tant que "root".
    if hasattr( os, "geteuid" ) : # Sinon, c'est qu'on est sous Windows
        if os.geteuid() == 0 : # UID de "root" = 0
            print( "Ce script ne peut pas être exécuté en tant que super-utilisateur." )
            print( "Ceci est un principe de sécurité." )
            sys.exit(0)
    
    # Vérification de l'existence du fichier des paramètres.
    try :
        import parameters as param
    except ModuleNotFoundError :
        print( "Fichier \"parameters.py\" introuvable !" )
        print( "Veuillez dupliquer \"parameters_sample.py\" vers \"parameters.py\", puis configurer ce-dernier." )
        sys.exit(0)
    
    
    # Importation des modules du serveur AOTF, ce qui permet de vérifier que
    # les librairies Python nécessaires sont installées.
    print( "Vérification des importations...")
    try :
        from app.check_parameters import check_parameters
        from app.class_Command_Line_Interface import Command_Line_Interface
        from app.class_Threads_Manager import Threads_Manager
    
    except ModuleNotFoundError as error :
        # Si c'est une vraie ModuleNotFoundError, elle contient le nom du module.
        if error.name != None and error.name != "" :
            print( f"Il manque la librairie suivante : {error.name}" )
            print( "Veuillez exécuter : pip install -r requirements.txt" )
        
        # Sinon, c'est nous qui l'avons créée, et donc elle a un message propre.
        # Voir par exemple le fichier "class_TweepyAbstraction.py" qui vérifie
        # la version de la librairie Tweepy.
        else :
            print( "Il y a eu un problème lors de la vérification des librairies." )
            print( error )
        sys.exit(0)
    
    else :
        print( "Toutes les librairies nécessaires sont présentes !" )
    
    
    # Initialiser le gestionnaire des threads.
    # Avant de vérifier les paramètres, afin qu'il gère les signaux.
    threads_manager = Threads_Manager()
    
    # Vérification des paramètres.
    # Voir le fichier "check_parameters.py".
    if not check_parameters() : sys.exit(0)
    
    # Lancer le serveur de mémoire partagée et les threads.
    # Voir le fichier "class_Threads_Manager.py".
    threads_manager.launch_threads()
    shared_memory = threads_manager._shared_memory
    
    
    # On s'enregistre comme thread / processus.
    # Note : Pyro crée aussi pleins de threads (Mais pas des processus comme
    # nous en mode multi-processus) qui ne sont pas enregistrés dans notre
    # registre des threads. Et ce n'est pas grave.
    shared_memory.threads_registry.register_thread( "app.py", os.getpid() )
    
    # Exécuter le back-end, c'est à dire l'entrée en ligne de commande (CLI).
    cli = Command_Line_Interface( shared_memory )
    cli.do_cli_loop()
    
    # Si on est sorti de la boucle de la CLI, c'est que la commande "stop" a
    # été exécutée. On peut donc lancer la procédure d'arrêt de serveur AOTF.
    threads_manager.stop_threads()
