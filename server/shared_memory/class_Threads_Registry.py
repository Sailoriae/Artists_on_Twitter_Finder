#!/usr/bin/python3
# coding: utf-8

import Pyro4

try :
    from open_proxy import open_proxy
except ModuleNotFoundError :
    from .open_proxy import open_proxy


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
        if not thread_name in self._pid_dict :
            raise RuntimeError( f"Le thread \"{thread_name}\" n'a pas été enregistré !" )
        if request == None :
            self._requests_dict[ thread_name ] = None
        else :
            self._requests_dict[ thread_name ] = request.get_URI()
    
    """
    @param thread_name L'identifiant du thread.
    @return Un proxy vers la requête qu'il est en train de traiter, ou None si
            aucune requête n'est associée au thread.
    """
    def get_request ( self, thread_name ) :
        if not thread_name in self._pid_dict :
            raise RuntimeError( f"Le thread \"{thread_name}\" n'a pas été enregistré !" )
        if not thread_name in self._requests_dict :
            return None
        if self._requests_dict[ thread_name ] == None :
            return None
        return open_proxy( self._requests_dict[ thread_name ] )
    
    """
    @return Une chaine de caractères à afficher, indiquant le status de tous
            les threads.
    """
    def get_status ( self ) :
        to_print = ""
        sorted_dict = sorted( self._pid_dict.items() )
        for (key, value) in sorted_dict :
            # Affichage identique pour tous les threads
            to_print += f"[PID {value}] " + key
            
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
                request = open_proxy( request )
                
                # Afficher un thread de traitement des requêtes utilisateurs
                if request.request_type == "user" : 
                    to_print += f" : {request.input_url}\n"
                
                # Afficher un thread de traitement des requêtes de scan
                elif request.request_type == "scan" :
                    to_print += f" : @{request.account_name} (ID {request.account_id})"
                    
                    # Thread d'indexation des Tweets trouvés avec l'API de recherche
                    if "thread_step_C_SearchAPI_index_account_tweets" in key :
                        to_print += f", {request.SearchAPI_tweets_queue.qsize()} Tweets restant\n"
                    # Thread d'indexation des Tweets trouvés avec l'API de timeline
                    elif "thread_step_D_TimelineAPI_index_account_tweets" in key :
                        to_print += f", {request.TimelineAPI_tweets_queue.qsize()} Tweets restant\n"
                    else :
                        to_print += "\n"
        
        return to_print
