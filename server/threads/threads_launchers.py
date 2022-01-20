#!/usr/bin/python3
# coding: utf-8

import os
import sys
import signal
import threading
import multiprocessing
from datetime import datetime
import traceback
import Pyro4

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
    
    def on_sighup ( signum, frame ) :
        sys.stdout = open( os.devnull, "w" )
    
    try : signal.signal(signal.SIGHUP, on_sighup)
    except AttributeError : pass # Windows
    
    threads_list = procedure( *arguments )
    
    try :
        subprocess_procedure( threads_list, arguments[-1] )
    except Exception :
        error_name = "Erreur dans la procédure d'un processus fils !\n"
        error_name +=  f"S'est produite le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.\n"
        
        file = open( "subprocess_procedure_errors.log", "a" )
        file.write( "ICI LE COLLECTEUR D'ERREURS DES PROCESSUS FILS !\n" )
        file.write( "Je suis dans le fichier suivant : threads/threads_launcher.py\n" )
        file.write( error_name )
        traceback.print_exc( file = file )
        file.write( "\n\n\n" )
        file.close()
        
        print( error_name )
        traceback.print_exc()
    
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
    Pyro4.config.SERIALIZER = "pickle"
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
@param thread_id ID du thread ou de la procédure.
@param in_process False pour le lancer directement,
                  True pour le lancer seul dans un processus fils.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Thread XOR processus créé.
"""
def launch_thread( thread_procedure, thread_id : int, in_process : bool, shared_memory_uri : str ) :
    if in_process and param.ENABLE_MULTIPROCESSING :
        thread_or_process = multiprocessing.Process(
            name = f"{thread_procedure.__name__}_th{thread_id}_container",
            target = subprocess,
            args = ( os.getpid(), _launch_subprocess_thread, thread_procedure, thread_id, shared_memory_uri ) )
    else :
        thread_or_process = threading.Thread(
            name = f"{thread_procedure.__name__}_th{thread_id}",
            target = error_collector,
            args = ( thread_procedure, thread_id, shared_memory_uri ) )
    
    thread_or_process.start()
    return thread_or_process

# Lancer un thread qui est seul dans un processus fils
# Cette fonction peut être appelée uniquement par "subprocess()"
def _launch_subprocess_thread( thread_procedure, thread_id, shared_memory_uri ) :
    return [ launch_thread( thread_procedure, thread_id, False, shared_memory_uri ) ]


"""
Lancer plusieurs threads identiques.
Ces procédures sont lancées dans le collecteur d'erreurs.

Si on est en mode multi-processus, ils sont lancés dans un processus conteneur.
Le paramètre "in_process" permet de définir si ils ont chacun leur processus
conteneur, ou s'ils en ont un pour tous.
Sinon, ils sont lancés directement en tant que threads.

@param thread_procedure Procédure à exécuter.
@param number_of_threads Nombre de fois qu'il faut lancer cette procédure,
                         c'est à dire le nombre de threads à créer.
@param in_process False pour les lancer tous dans le même processus fils,
                  True pour les lancer chacun dans un processus fils.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Liste des threads XOR processus créés.
"""
def launch_identical_threads_in_container( thread_procedure, number_of_threads, in_process, shared_memory_uri ) :
    # On crée un conteneur uniquement si ses enfants sont des threads
    if param.ENABLE_MULTIPROCESSING and not in_process :
        process = multiprocessing.Process(
            name = f"{thread_procedure.__name__}_th_container",
            target = subprocess,
            args = ( os.getpid(), _threads_container_for_identical_threads, thread_procedure, number_of_threads, in_process, shared_memory_uri ) )
        process.start()
        return [ process ]
    else :
        return _threads_container_for_identical_threads( thread_procedure,
                                                         number_of_threads,
                                                         in_process,
                                                         shared_memory_uri )

# Lancer plusieurs threads ou processus identiques
# En mode multi-processus, cette fonction est appelée par "subprocess()"
def _threads_container_for_identical_threads( thread_procedure, number_of_threads, in_process, shared_memory_uri ) :
    threads_or_process = []
    for i in range( number_of_threads ) :
        threads_or_process.append(
            launch_thread( thread_procedure, i+1, in_process, shared_memory_uri ) )
    return threads_or_process

"""
Lancer plusieurs threads différents.
Ces procédures sont lancées dans le collecteur d'erreurs.

Si on est en mode multi-processus, ils sont lancés dans un processus conteneur.
Le paramètre "in_process" permet de définir si ils ont chacun leur processus
conteneur, ou s'ils en ont un pour tous.
Sinon, ils sont lancés directement en tant que threads.

@param thread_procedures Liste des procédures à exécuter.
@param in_process False pour les lancer tous dans le même processus fils,
                  True pour les lancer chacun dans un processus fils.
@param container_name Nom du processus conteneur (Si "in_process = False").
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Liste des threads XOR processus créés.
"""
def launch_unique_threads_in_container( thread_procedures, in_process, container_name, shared_memory_uri ) :
    # On crée un conteneur uniquement si ses enfants sont des threads
    if param.ENABLE_MULTIPROCESSING and not in_process :
        process = multiprocessing.Process(
            name = f"{container_name}_th_container",
            target = subprocess,
            args = ( os.getpid(), _threads_container_for_unique_threads, thread_procedures, in_process, shared_memory_uri ) )
        process.start()
        return [ process ]
    else :
        return _threads_container_for_unique_threads( thread_procedures,
                                                      in_process,
                                                      shared_memory_uri )

# Lancer plusieurs threads ou processus différents
# En mode multi-processus, cette fonction est appelée par "subprocess()"
def _threads_container_for_unique_threads( thread_procedures, in_process, shared_memory_uri ) :
    threads_or_process = []
    counts = {} # Si il y a plusieurs fois la même procédure dans la liste
    for procedure in thread_procedures :
        if procedure in counts : counts[ procedure ] += 1
        else : counts[ procedure ] = 1
        threads_or_process.append(
            launch_thread( procedure, counts[ procedure ], in_process, shared_memory_uri ) )
    return threads_or_process
