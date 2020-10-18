#!/usr/bin/python3
# coding: utf-8

import traceback

try :
    from class_Shared_Memory import Shared_Memory
except ModuleNotFoundError :
    from .class_Shared_Memory import Shared_Memory


"""
Voir la classe Shared_Memory pour la doc des paramètres.
"""
def thread_pyro_server( pyro_port = 3300, pool_size = 100000 ) :
    try :
        shared_memory = Shared_Memory( pyro_port, pool_size )
        
        print( "Démarrage du serveur de mémoire partagée Pyro..." )
        shared_memory.launch_pyro_server()
        print( "Serveur de mémoire partagée Pyro arrêté !" )
    
    except Exception :
        file = open( "thread_pyro_server_errors.log", "a" )
        file.write( "Erreur dans le serveur de mémoire partagée Pyro !\n" )
        file.write( "Si vous voyez ceci, c'est que c'est vraiment la merde.\n" )
        traceback.print_exc( file = file )
        file.write( "\n\n\n" )
        file.close()


if __name__ == "__main__" :
    thread_pyro_server()
