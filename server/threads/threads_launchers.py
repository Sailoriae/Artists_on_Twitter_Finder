#!/usr/bin/python3
# coding: utf-8

import os
import sys
import signal
import threading
import multiprocessing

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


"""
Fonction racine à un processus fils du serveur AOTF.
Lorsqu'on crée un nouveau processus, il faut qu'il puisse gérer les SIGTERM, et
en envoyer vers "app.py" afin d'arrêter le serveur AOTF.
Il faut aussi qu'il puisse gérer les SIGHUP lorsque STDOUT n'existe plus, mais
ne l'envoie pas vers "app.py".

@param parent_pid PID du processus père.
@param procedure Procédure à exécuter.
@param *arguments Arguments à passer à cette procédure.
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
    
    procedure( *arguments )


"""
Lancer un thread ou un processus sans conteneur.

@param thread_procedure Procédure à exécuter.
@param thread_id ID du thread ou de la procédure.
@param as_process False pour les lancer en tant que threads,
                  True pour les lancer en tant que processus.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Thread ou processus créé.
"""
def launch_thread( thread_procedure, thread_id : int, as_process : bool, shared_memory_uri : str ) :
    if as_process and param.ENABLE_MULTIPROCESSING :
        thread_or_process = multiprocessing.Process(
            name = f"{thread_procedure.__name__}_th{thread_id}",
            target = subprocess,
            args = ( os.getpid(), error_collector, thread_procedure, thread_id, shared_memory_uri ) )
    else :
        thread_or_process = threading.Thread(
            name = f"{thread_procedure.__name__}_th{thread_id}",
            target = error_collector,
            args = ( thread_procedure, thread_id, shared_memory_uri ) )
    
    thread_or_process.start()
    return thread_or_process


"""
Lancer plusieurs threads ou processus identiques.
Ces procédures sont lancées dans le collecteur d'erreurs.

Si ils sont lancés en tant que threads ("as_process" est à "False") et que
"ENABLE_MULTIPROCESSING" est à "True", les threads sont lancés dans un unique
processus conteneur. Cette fonction retourne alors ce processus
Sinon, cette fonction retourne la liste des threads ou procédures créés.

@param thread_procedure Procédure à exécuter.
@param number_of_threads Nombre de fois qu'il faut lancer cette procédure,
                         c'est à dire le nombre de threads à créer.
@param as_process False pour les lancer en tant que threads,
                  True pour les lancer en tant que processus, aucun processus
                  conteneur ne sera lancé.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Liste contenant uniquement le processus conteneur,
        Ou liste des threads ou processus créés.
"""
def launch_identical_threads_in_container( thread_procedure, number_of_threads, as_process, shared_memory_uri ) :
    # On crée un conteneur uniquement si ses enfants sont des threads
    if param.ENABLE_MULTIPROCESSING and not as_process :
        process = multiprocessing.Process(
            name = f"{thread_procedure.__name__}_th_container",
            target = subprocess,
            args = ( os.getpid(), _threads_container_for_identical_threads, thread_procedure, number_of_threads, as_process, shared_memory_uri ) )
        process.start()
        return [ process ]
    else :
        return _threads_container_for_identical_threads( thread_procedure,
                                                         number_of_threads,
                                                         as_process,
                                                         shared_memory_uri,
                                                         is_a_process = False )

def _threads_container_for_identical_threads( thread_procedure, number_of_threads, as_process, shared_memory_uri, is_a_process = False ) :
    threads_or_process = []
    for i in range( number_of_threads ) :
        threads_or_process.append(
            launch_thread( thread_procedure, i+1, as_process, shared_memory_uri ) )
    if not is_a_process :
        return threads_or_process
    for thread in threads_or_process :
        thread.join()

"""
Lancer plusieurs threads ou processus différents.
Ces procédures sont lancées dans le collecteur d'erreurs.

Si ils sont lancés en tant que threads ("as_process" est à "False") et que
"ENABLE_MULTIPROCESSING" est à "True", les threads sont lancés dans un unique
processus conteneur. Cette fonction retourne alors ce processus
Sinon, cette fonction retourne la liste des threads ou procédures créés.

@param thread_procedures Liste des procédures à exécuter.
@param as_process False pour les lancer en tant que threads,
                  True pour les lancer en tant que processus, aucun processus
                  conteneur ne sera lancé.
@param container_name Nom du processus conteneur.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.

@return Liste des threads ou processus créés.
"""
def launch_unique_threads_in_container( thread_procedures, as_process, container_name, shared_memory_uri ) :
    # On crée un conteneur uniquement si ses enfants sont des threads
    if param.ENABLE_MULTIPROCESSING and not as_process :
        process = multiprocessing.Process(
            name = f"{container_name}_th_container",
            target = subprocess,
            args = ( os.getpid(), _threads_container_for_unique_threads, thread_procedures, as_process, shared_memory_uri ) )
        process.start()
        return [ process ]
    else :
        return _threads_container_for_unique_threads( thread_procedures,
                                                      as_process,
                                                      shared_memory_uri,
                                                      is_a_process = False )

def _threads_container_for_unique_threads( thread_procedures, as_process, shared_memory_uri, is_a_process = True ) :
    threads_or_process = []
    for procedure in thread_procedures :
        threads_or_process.append(
            launch_thread( procedure, 1, as_process, shared_memory_uri ) )
    if not is_a_process :
        return threads_or_process
    for thread in threads_or_process :
        thread.join()
