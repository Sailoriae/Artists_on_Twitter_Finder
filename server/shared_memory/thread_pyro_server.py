#!/usr/bin/python3
# coding: utf-8

import traceback
from datetime import datetime

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

from shared_memory.class_Shared_Memory import Shared_Memory


"""
Permet de lancer la mémoire partagée en tant que serveur Pyro.
A utiliser uniquement si le serveur est lancé en mode multi-processus. Sinon,
utiliser directement l'objet Shared_Memory (A instancier qu'une seule fois).
Voir la classe Shared_Memory pour la doc des paramètres.
"""
def thread_pyro_server( pyro_port = 3300, pool_size = 100000 ) :
    try :
        shared_memory = Shared_Memory( pyro_port, pool_size )
        # La classe "Threads_Registry" se charge d'enregistrer le thread du serveur Pyro
        
        print( "[pyro_server_th1] Démarrage du serveur de mémoire partagée Pyro..." )
        shared_memory.launch_pyro_server()
        print( "[pyro_server_th1] Serveur de mémoire partagée Pyro arrêté !" )
    
    except Exception as error :
        error_name = "Erreur dans le serveur de mémoire partagée Pyro !\n"
        error_name +=  f"S'est produite le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.\n"
        error_name +=  "Si vous voyez ceci, c'est que c'est vraiment la merde.\n"
        
        file = open( "thread_pyro_server_errors.log", "a" )
        file.write( "ICI LE COLLECTEUR D'ERREURS DE LA MEMOIRE PARTAGEE !\n" )
        file.write( "Je suis dans le fichier suivant : shared_memory/thread_pyro_server.py\n" )
        file.write( error_name )
        traceback.print_exc( file = file )
        file.write( "\n\n\n" )
        file.close()
        
        print( error_name, end = "" )
        print( error )
        print( "La pile d'appel complète a été écrite dans un fichier." )


if __name__ == "__main__" :
    thread_pyro_server()
