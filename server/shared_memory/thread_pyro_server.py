#!/usr/bin/python3
# coding: utf-8

try :
    from class_Shared_Memory import Shared_Memory
except ModuleNotFoundError :
    from .class_Shared_Memory import Shared_Memory


"""
Voir la classe Shared_Memory pour la doc des paramètres.
"""
def thread_pyro_server( pyro_port = 3300, pool_size = 100000 ) :
    shared_memory = Shared_Memory( pyro_port, pool_size )
    
    print( "Démarrage du serveur de mémoire partagée Pyro..." )
    shared_memory.launch_pyro_server()
    print( "Serveur de mémoire partagée Pyro arrêté !" )


if __name__ == "__main__" :
    thread_pyro_server()
