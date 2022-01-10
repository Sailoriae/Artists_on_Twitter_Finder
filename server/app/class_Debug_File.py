#!/usr/bin/python3
# coding: utf-8

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


"""
Classe du fichier de débug. Il permet d'obtenir des informations sur le serveur
qu'on ne peut pas voir via un terminal (Et donc la ligne de commande). Par
exemple lors du "shutdown" du système d'exploitation, pour visualiser si AOTF
reçoit bien un sinal SIGTERM et s'arrête proprement.

Le fichier de débug ne fonctionne que si le paramètre "DEBUG" est sur "True. De
plus, il est ouvert avec un buffer de ligne (Vidé à chaque "\n").
"""
class Debug_File :
    """
    Constructeur, ouvre le fichier de débug.
    """
    def __init__ ( self ) :
        if not param.DEBUG : return
        self._file = open( "debug.log", "a", buffering = 1 )
    
    """
    Ecrire une ligne dans le fichier de débug.
    """
    def write ( self, line ) :
        if not param.DEBUG : return
        try : self._file.write( line + "\n" )
        except Exception : pass # Mesure de sécurité
    
    """
    Fermer proprement le fichier de débug.
    """
    def close ( self ) :
        if not param.DEBUG : return
        if self._file.closed : return
        try : self._file.close()
        except Exception : pass # Mesure de sécurité
    
    """
    Destructeur, ferme le fichier de débug.
    """
    def __del__ ( self ) :
        self.close()
