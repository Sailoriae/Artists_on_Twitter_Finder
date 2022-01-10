#!/usr/bin/python3
# coding: utf-8

import Pyro4
import os
import psutil

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

from shared_memory.open_proxy import open_proxy
import parameters as param


"""
Objet pour que les thread enregistrent la requête qu'ils sont en train de
traiter.
ATTENTION : Un thread est un processus en mode multi-processus !
ATTENTION : Pyro crée aussi pleins de threads (Mais pas des processus comme
nous en mode multi-processus) qui ne sont pas enregistrés ici !
"""
@Pyro4.expose
class Threads_Registry :
    def __init__ ( self, root_shared_memory ) :
        self._root = root_shared_memory
        
        # Dictionnaire associant les threads à leur PID.
        self._pid_dict = {}
        
        # Dictionnaire associant les threads à l'URI de la requête qu'il est en
        # train de traiter.
        self._requests_dict = {}
        
        # Se charger d'enregistrer le thread du serveur Pyro
        # Respecte la convention de nommage des threads
        self.register_thread( "thread_pyro_server_th1", os.getpid() )
    
    """
    Enregistrer un thread / un processus.
    @param thread_name L'identifiant du thread.
    """
    def register_thread ( self, thread_name : str, pid : int ) :
        if thread_name in self._pid_dict :
            raise AssertionError( f"Le thread \"{thread_name}\" a déjà été enregistré !" )
        self._pid_dict[ thread_name ] = str(pid)
    
    """
    @param thread_name L'identifiant du thread.
    @param request Le proxy vers la requête qu'il est en train de traiter, ou
                   None s'il est en attente.
    """
    def set_request ( self, thread_name, request ) :
        if not thread_name in self._pid_dict :
            raise AssertionError( f"Le thread \"{thread_name}\" n'a pas été enregistré !" )
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
            raise AssertionError( f"Le thread \"{thread_name}\" n'a pas été enregistré !" )
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
        total_memory_size = 0
        pid_memory_size = [] # Liste des PID déjà comptés dans "total_memory_size"
        
        # Trier par nom du thread
        sorted_dict = sorted( self._pid_dict.items() )
        
        # Regrouper les threads par PID
        pids_threads = {}
        for (thread, pid) in sorted_dict :
            if not pid in pids_threads :
                pids_threads[pid] = []
            pids_threads[pid].append( thread )
        
        # Reconstruire le dictionnaire des threads
        # Ils seront regroupés par PID et triés par noms
        sorted_dict = {}
        for pid in pids_threads :
            for thread in pids_threads[pid] :
                sorted_dict[thread] = pid
        
        # Construire la chaine à afficher
        last_pid = None
        for thread in sorted_dict :
            pid = sorted_dict[thread]
            
            # Affichage identique pour tous les threads
            if pid == last_pid :
                to_print += " " * ( len(str(pid))+5 ) + "∟ " + thread
            else :
                to_print += f"[PID {pid}] " + thread
            last_pid = pid
            
            # Affichage du poid en mémoire du thread
            # On vérifie de ne pas compter deux fois le même PID
            if param.ENABLE_MULTIPROCESSING and not int(pid) in pid_memory_size :
                process_size = psutil.Process( int(pid) ).memory_info().rss # en octets
                process_size = process_size / 1024 / 1024 # en megaoctets
                to_print += " ({:.2f} Mo)".format( process_size )
                total_memory_size += process_size
                pid_memory_size.append( int(pid) )
            
            try :
                request = self._requests_dict[thread]
            
            
            except KeyError :
                # Afficher un thread d'indexation (Etape C)
                if "thread_step_C_index_account_tweets" in thread :
                    tweet_id, account_id = self._root._scan_requests_obj.get_indexing_ids( thread )
                    if tweet_id != None :
                        to_print += f" : Tweet ID {tweet_id}\n"
                    else :
                        to_print += " : IDLE\n"
                
                # Afficher un thread spécial (C'est à dire un thread qui n'est pas
                # un thread de traitement)
                else :
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
                    to_print += f" : @{request.account_name} (ID {request.account_id})\n"
        
        if not param.ENABLE_MULTIPROCESSING :
            total_memory_size = psutil.Process( os.getpid() ).memory_info().rss # en octets
            total_memory_size = total_memory_size / 1024 / 1024 # en megaoctets
        
        to_print += "Taille totale d'AOTF en mémoire : {:.2f} Mo".format( total_memory_size )
        
        return to_print
