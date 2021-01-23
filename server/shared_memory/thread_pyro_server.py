#!/usr/bin/python3
# coding: utf-8

import traceback

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( ".." )

from shared_memory.class_Shared_Memory import Shared_Memory


"""
Permet de lancer la mémoire partagée en tant que serveur PYRO.
A utiliser uniquement si le serveur est lancé en mode multi-processus. Sinon,
utiliser directement l'objet Shared_Memory (A instancier qu'une seule fois).
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
