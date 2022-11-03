#!/usr/bin/python3
# coding: utf-8

import Pyro5 # Pour Pyro5.config
import Pyro5.errors
import threading
from random import randint
from time import sleep

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

from shared_memory.thread_pyro_server import thread_pyro_server
from shared_memory.class_Shared_Memory import Shared_Memory
from shared_memory.open_proxy import open_proxy


"""
Fonction d'initialisation de la mémoire partagée. Lance son thread et ainsi le
serveur Pyro si on est en mode multi-processus, ou sinon instancie simplement
son objet racine.

@param pool_size Nombre maximum de proxies ouvrables (Si multi-proxessus).
                 Note : Un thread est créé à chaque connexion au serveur Pyro.

@return Un tuple contenant les données suivantes :
        - Proxy vers la mémoire partagée, ou objet racine.
          Ou "None" si le lancement de la mémoire partagée a échoué.
        - Objets de thread du serveur Pyro.
          Ou "None" si on n'est pas en mode multi-processus.
"""
def launch_shared_memory ( pool_size : int ) :
    if param.ENABLE_MULTIPROCESSING :
        return _launch_with_pyro( pool_size )
    else :
        return _launch_without_pyro()


"""
Lancement de la mémoire partagée avec le serveur Pyro.

@return Un tuple contenant les données suivantes :
        - Proxy vers la mémoire partagée.
          Ou "None" si le lancement de la mémoire partagée a échoué.
        - Objets de thread du serveur Pyro.
"""
def _launch_with_pyro ( pool_size : int ) :
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
    thread_pyro = threading.Thread( name = "thread_pyro_server_th1",
                                    target = thread_pyro_server,
                                    args = ( pyro_port, pool_size ) )
    thread_pyro.start()
    
    # On prépare la connexion au serveur.
    Pyro5.config.SERIALIZER = "serpent"
    shared_memory_uri = "PYRO:shared_memory@localhost:" + str( pyro_port )
    
    # On test pendant 30 secondes que la connection s'établisse.
    shared_memory = None
    for i in range( 30 ) :
        print( "Connexion au serveur de mémoire partagée..." )
        try :
            shared_memory = open_proxy( shared_memory_uri )
            shared_memory.keep_threads_alive # Test d'accès
        except ( Pyro5.errors.ConnectionClosedError,
                 Pyro5.errors.CommunicationError,
                 ConnectionRefusedError ) :
            sleep(1)
        else :
            print( "Connexion au serveur de mémoire partagée réussie !" )
            break
    
    if shared_memory == None :
        print( "Connexion au serveur de mémoire partagée impossible !" )
        return None, thread_pyro
    
    return shared_memory, thread_pyro


"""
Lancement de la mémoire partagée sans le serveur Pyro.

@return Un tuple contenant les données suivantes :
        - Objet racine de la mémoire partagée.
        - "None", car on n'est pas en mode multi-processus.
"""
def _launch_without_pyro () :
    shared_memory = open_proxy( Shared_Memory( 0, 0 ) )
    return shared_memory, None
