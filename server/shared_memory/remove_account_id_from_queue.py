#!/usr/bin/python3
# coding: utf-8

import queue

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

from shared_memory.class_Pyro_Queue import Pyro_Queue


"""
Supprimer la requête d'un compte Twitter d'une file d'attente de scan.
@param queue La file d'attente à traiter, sous forme d'objet Pyro_Queue.
             Attention : Ne doit pas être un proxy vers cet objet !
@param account_id L'ID du compte Twitter dont la requête est à supprimer.
"""
def remove_account_id_from_queue ( input_queue : Pyro_Queue, account_id : int ) :
    # On utilise un objet Pyro_Queue() pour la conversion des URI lors de
    # l'utilisation de la méthode put().
    temp_queue = Pyro_Queue( convert_uri = convert_uri._convert_uri )
    
    while True :
        try :
            # Passer par la méthode get() qui nous ouvre les proxies.
            request = input_queue.get( block = False )
        except queue.Empty :
            request = None
        if request == None :
            input_queue._queue = temp_queue._queue
            return
        if request.account_id != account_id :
            temp_queue.put( request )
