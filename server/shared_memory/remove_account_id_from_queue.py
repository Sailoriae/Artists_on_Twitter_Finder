#!/usr/bin/python3
# coding: utf-8

import queue


"""
Supprimer la requête d'un compte Twitter d'une file d'attente de scan.
@param queue La file d'attente à traiter, sous forme d'objet Pyro_Queue.
             Attention : Ne doit pas être un proxy vers cet objet !
@param account_id L'ID du compte Twitter dont la requête est à supprimer.
"""
def remove_account_id_from_queue ( input_queue, account_id ) :
    new_queue = queue.Queue()
    while True :
        try :
            request = input_queue.get( block = False ) # Passer par la méthode get() qui nous ouvre les proxies
        except queue.Empty :
            input_queue._queue = new_queue
            return
        else :
            if request.account_id != account_id :
                new_queue.put( request )
