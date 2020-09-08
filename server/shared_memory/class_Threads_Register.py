#!/usr/bin/python3
# coding: utf-8

import Pyro4


"""
Objet pour que les thread enregistrent la requête qu'ils sont en train de
traiter.
"""
@Pyro4.expose
class Threads_Register :
    def __init__ ( self ) :
        # Dictionnaire associant les threads à l'URI de la requête qu'il est en
        # train de traiter.
        self._dict = {}
    
    """
    @param thread_name L'identifiant du thread.
    @param request Le proxy vers la requête qu'il est en train de traiter, ou
                   None s'il est en attente.
    """
    def set_request ( self, thread_name, request ) :
        if request == None :
            self._dict[ thread_name ] = None
        else :
            self._dict[ thread_name ] = request._pyroUri.asString()
    
    """
    @param thread_name L'identifiant du thread.
    """
    def get_request ( self, thread_name ) :
        return Pyro4.Proxy( self._dict[ thread_name ] )
    
    """
    @return Une chaine de caractères à afficher, indiquant le status de tous
            les threads.
    """
    def get_status ( self ) :
        to_print = ""
        sorted_dict = sorted( self._dict.items() )
        for (key, value) in sorted_dict :
            if value == None :
                to_print += key + " : IDLE\n"
            else :
                value = Pyro4.Proxy( value )
                try : # Afficher un thread de traitement des requêtes utilisateurs
                    to_print += key + " : " + value.input_url + "\n"
                except AttributeError :
                    try : # Afficher un thread de traitement des requêtes de scan
                        to_print += key + " : @" + value.account_name + " (ID " + str(value.account_id) + ")\n"
                    except AttributeError :
                        continue
        return to_print
