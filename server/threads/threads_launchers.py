#!/usr/bin/python3
# coding: utf-8

import os
import sys
import signal
import threading
import multiprocessing
from datetime import datetime
import traceback
import Pyro5 # Pour Pyro5.config
import Pyro5.errors

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
from threads.error_collector import error_collector
from shared_memory.open_proxy import open_proxy


"""
Fonction racine à un processus fils du serveur AOTF.
Lorsqu'on crée un nouveau processus, il faut qu'il puisse gérer les SIGTERM, et
en envoyer vers "app.py" afin d'arrêter le serveur AOTF.
Il faut aussi qu'il puisse gérer les SIGHUP lorsque STDOUT n'existe plus, mais
ne l'envoie pas vers "app.py".
Enfin, il peut gérer les ordre venant de la mémoire partagée.

@param parent_pid PID du processus père.
@param procedure Procédure à exécuter. Doit retourner une liste de threads !
@param *arguments Arguments à passer à cette procédure. Le dernier est toujours
                  l'URI de l'objet racine de la mémoire partagée
"""
def subprocess ( parent_pid, procedure, *arguments ) :
    def on_sigterm ( signum, frame ) :
        try :
            os.kill(parent_pid, signal.SIGTERM)
        except OSError : # Le père est déjà mort
            sys.exit(0)
    
    signal.signal(signal.SIGINT, on_sigterm)
    signal.signal(signal.SIGTERM, on_sigterm)
    
    # Voir "Threads_Manager.on_sigterm()"
    def on_sighup ( signum, frame ) :
        if param.DEBUG :
            sys.stdout = open( "sighup.log", "a", buffering = 1 ) # Vider le buffer à chaque "\n"
    
    try : signal.signal(signal.SIGHUP, on_sighup)
    except AttributeError : pass # Windows
    
    threads_list = procedure( *arguments )
    
    try :
        subprocess_procedure( threads_list, arguments[-1] )
    except Exception as error :
        # Si le processus racine a été tué, on peut s'arrêter maintenant
        # On le détecte avec une erreur de connexion au serveur Pyro
        # On ne peut pas le détecter avec le PID
        if isinstance( error, Pyro5.errors.CommunicationError ) :
            sys.exit(0) # Nos threads ont leur attribut "daemon" à "True"
        
        error_name = f"Erreur dans la procédure du processus fils PID {os.getpid()} !\n"
        error_name +=  f"S'est produite le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.\n"
        
        file = open( "subprocess_procedure_errors.log", "a" )
        file.write( "ICI LE COLLECTEUR D'ERREURS DES PROCESSUS FILS !\n" )
        file.write( "Je suis dans le fichier suivant : threads/threads_launcher.py\n" )
        file.write( error_name )
        traceback.print_exc( file = file )
        file.write( "\n\n\n" )
        file.close()
        
        print( error_name, end = "" )
        print( f"{type(error).__name__}: {error}" )
        print( "La pile d'appel complète a été écrite dans un fichier." )
    
    # Note : Les threads s'arrêtent si la mémoire partagée leur en a donné
    # l'ordre, ou bien s'ils ont planté parce que celle-ci n'est plus
    # accesssible (Beaucoup de fichiers logs seront alors générés).
    for thread in threads_list :
        thread.join()


"""
Boucle de travail d'un processus fils du serveur AOTF, permettant d'écouter
les ordres venenant de la mémoire partagée.

@param threads_list Liste des threads que nous éxécutons.
@param shared_memory_uri URI de la racine du serveur Pyro.
"""
def subprocess_procedure ( threads_list, shared_memory_uri ) :
    # On est ici forcément en mode multi-processus
    Pyro5.config.SERIALIZER = "serpent"
    shared_memory = open_proxy( shared_memory_uri )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_processes_registry = shared_memory.processes_registry
    
    # S'enregistrer en tant que processus fils
    shared_memory_processes_registry.register_process( os.getpid() )
    
    while shared_memory.keep_threads_alive :
        # Cette fonction contient les temps d'attente
        message = shared_memory_processes_registry.get_message( os.getpid() )
        
        # Ordre d'écriture des piles d'éxécution de nos threads
        if message == "write_stacks" :
            write_stacks( threads_list )

def write_stacks ( threads_list ) :
    for thread in threads_list :
        to_write = f"[PID {os.getpid()}] Procédure {thread.name} le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')} :\n"
        to_write += "".join( traceback.format_stack( sys._current_frames()[thread.ident] ) )
        to_write += "\n\n\n"
        file = open( "stacktrace.log", "a", encoding = "utf-8" )
        file.write( to_write )
        file.close()


"""
Lancer un thread seul.
Cette procédure est lancée dans le collecteur d'erreurs.

@param thread_procedure Procédure à exécuter.
@param procedure_id ID de la procédure. Doit être uniquement si elle est lancée
                    plusieurs fois, c'est à dire dans plusieurs threads.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Thread XOR processus créé.
"""
def launch_thread( thread_procedure, procedure_id : int, shared_memory_uri : str ) :
    thread = threading.Thread(
        name = f"{thread_procedure.__name__}_th{procedure_id}",
        target = error_collector,
        args = ( thread_procedure, procedure_id, shared_memory_uri ) )
    
    # Par défaut, si le processus se termine, Python s'arrête lorsqe tous les
    # threads ont terminé. Ce comportement est embêtant dans le cas de l'arrêt
    # du serveur AOTF, surtout qu'on fait des "joint()" proprement.
    # On désactive donc ce comportement. Ainsi, les threads s'arrêtent lorsque
    # le processus arrive au bout de ses instruction.
    thread.daemon = True
    
    thread.start()
    return thread


"""
Lancer plusieurs threads.
Ces procédures sont lancées dans le collecteur d'erreurs.

@param thread_procedures Liste des procédures à exécuter, associées à leur ID.
                         Les ID doivent être uniques si une même procédure est
                         lancée plusieurs fois (Donc dans plusieurs threads).
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Liste des threads créés.
"""
def launch_threads( thread_procedures, shared_memory_uri ) :
    threads = []
    for procedure, procedure_id in thread_procedures :
        threads.append(
            launch_thread( procedure, procedure_id, shared_memory_uri ) )
    return threads


"""
Lancer plusieurs threads dans un seul processus conteneur.
Ces procédures sont lancées dans le collecteur d'erreurs.

Peut aussi être utilisé pour lancer un thread seul dans un processus conteneur.

Si on n'est pas en mode multi-processus, il n'y a pas de processus conteneur,
et les threads sont lancés directement.

@param thread_procedures Liste des procédures à exécuter, associées à leurs ID.
                         Les ID doivent être uniques si une même procédure est
                         lancée plusieurs fois (Donc dans plusieurs threads).
@param container_name Nom du processus conteneur.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Liste des threads XOR processus créés.
"""
def launch_threads_in_container( thread_procedures, container_name, shared_memory_uri ) :
    if param.ENABLE_MULTIPROCESSING :
        process = multiprocessing.Process(
            name = container_name,
            target = subprocess,
            args = ( os.getpid(), launch_threads, thread_procedures, shared_memory_uri ) )
        process.start()
        return [ process ]
    else :
        return launch_threads( thread_procedures,
                               shared_memory_uri )
