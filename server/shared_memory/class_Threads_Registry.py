#!/usr/bin/python3
# coding: utf-8

import Pyro4


"""
Objet pour que les thread enregistrent la requête qu'ils sont en train de
traiter.
ATTENTION : Un thread est un processus en mode Multiprocessing !
ATTENTION : Pyro crée aussi pleins de threads (Mais pas des processus comme
nous en mode Multiprocessing) qui ne sont pas enregistrés ici !
"""
@Pyro4.expose
class Threads_Registry :
    def __init__ ( self ) :
        # Dictionnaire associant les threads à leur PID.
        self._pid_dict = {}
        
        # Dictionnaire associant les threads à l'URI de la requête qu'il est en
        # train de traiter.
        self._requests_dict = {}
    
    """
    Enregistrer un thread / un processus.
    @param thread_name L'identifiant du thread.
    """
    def register_thread ( self, thread_name : str, pid : int ) :
        self._pid_dict[ thread_name ] = str(pid)
    
    """
    @param thread_name L'identifiant du thread.
    @param request Le proxy vers la requête qu'il est en train de traiter, ou
                   None s'il est en attente.
    """
    def set_request ( self, thread_name, request ) :
        if request == None :
            self._requests_dict[ thread_name ] = None
        else :
            self._requests_dict[ thread_name ] = request._pyroUri.asString()
    
    """
    @param thread_name L'identifiant du thread.
    """
    def get_request ( self, thread_name ) :
        return Pyro4.Proxy( self._requests_dict[ thread_name ] )
    
    """
    @return Une chaine de caractères à afficher, indiquant le status de tous
            les threads.
    """
    def get_status ( self ) :
        to_print = ""
        sorted_dict = sorted( self._pid_dict.items() )
        for (key, value) in sorted_dict :
            # Affichage identique pour tous les threads
            to_print += "[PID " + value + "] " + key
            
            try :
                request = self._requests_dict[key]
            
            # Afficher un thread spécial (C'est à dire un thread qui n'est pas
            # un thread de traitement)
            except KeyError :
                to_print += "\n"
                continue
            
            if request == None :
                to_print += " : IDLE\n"
            else :
                request = Pyro4.Proxy( request )
                
                # Afficher un thread de traitement des requêtes utilisateurs
                if request.request_type == "user" : 
                    to_print += " : " + request.input_url + "\n"
                
                # Afficher un thread de traitement des requêtes de scan
                elif request.request_type == "scan" :
                    to_print += " : @" + request.account_name + " (ID " + str(request.account_id) + ")"
                    
                    # Thread d'indexation des Tweets trouvés avec l'API de recherche
                    if "thread_step_C_SearchAPI_index_account_tweets" in key :
                        to_print += ", " + str(request.SearchAPI_tweets_queue.qsize()) + " Tweets restant\n"
                    # Thread d'indexation des Tweets trouvés avec l'API de timeline
                    elif "thread_step_D_TimelineAPI_index_account_tweets" in key :
                        to_print += ", " + str(request.TimelineAPI_tweets_queue.qsize()) + " Tweets restant\n"
                    else :
                        to_print += "\n"
        
        return to_print
