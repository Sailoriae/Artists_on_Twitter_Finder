#!/usr/bin/python3
# coding: utf-8

import queue

try :
    from class_Pyro_Queue import Pyro_Queue
except ModuleNotFoundError :
    from .class_Pyro_Queue import Pyro_Queue


"""
Supprimer la requête d'un compte Twitter d'une file d'attente.
@param queue La file d'attente à traiter.
@param account_id L'ID du compte Twitter dont la requête est à supprimer.
"""
def remove_account_id_from_queue ( old_queue, account_id ) :
    new_queue = Pyro_Queue( convert_uri = old_queue.convert_uri )
    while True :
        try :
            request = old_queue.get( block = False )
        except queue.Empty :
            return new_queue
        else :
            if request.account_id != account_id :
                new_queue.put( request )
