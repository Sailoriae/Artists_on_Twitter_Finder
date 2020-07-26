#!/usr/bin/python3
# coding: utf-8

import datetime
from time import sleep


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Suppression des anciennes requêtes terminées des objets Scan_Requests_Pipeline
et User_Requests_Pipeline.
"""
def thread_remove_finished_requests( thread_id : int, shared_memory ) :
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        # On dors une heure (1200*3 = 3600)
        for i in range( 1200 ) :
            sleep( 3 )
            if not shared_memory.keep_service_alive :
                break
        
        # On prend la date actuelle
        now = datetime.datetime.now()
        
        # ====================================================================
        # Pipeline des requêtes utilisateurs
        # ====================================================================
        
        # On bloque l'accès la liste des requêtes du Pipeline
        shared_memory.user_requests.requests_sem.acquire()
        
        # On filtre la liste des requêtes
        new_requests_list = []
        for request in shared_memory.user_requests.requests :
            if request.finished_date != None :
                # Si la date de fin est à moins de 24h de maintenant, on garde
                # cette requête
                if now - request.finished_date < datetime.timedelta( hours = 24 ) :
                    # Si la requête s'est terminée en erreur, on la garde au
                    # maximum 1h
                    if request.problem != None :
                        if now - request.finished_date < datetime.timedelta( hours = 1 ) :
                            new_requests_list.append( request )
                    else :
                        new_requests_list.append( request )
        
        # On installe la nouvelle liste
        shared_memory.user_requests.requests = new_requests_list
        
        # On débloque l'accès à la liste des requêtes du Pipeline
        shared_memory.user_requests.requests_sem.release()
        
        # ====================================================================
        # Pipeline des requêtes de scan
        # ====================================================================
        
        # On bloque l'accès la liste des requêtes du Pipeline
        shared_memory.scan_requests.requests_sem.acquire()
        
        # On filtre la liste des requêtes
        new_requests_list = []
        for request in shared_memory.scan_requests.requests :
            if request.finished_date != None :
                # Si la date de fin est à moins de 24h de maintenant, on garde
                # cette requête
                if now - request.finished_date < datetime.timedelta( hours = 24 ) :
                    new_requests_list.append( request )
        
        # On installe la nouvelle liste
        shared_memory.scan_requests.requests = new_requests_list
        
        # On débloque l'accès à la liste des requêtes du Pipeline
        shared_memory.scan_requests.requests_sem.release()
    
    print( "[remove_finished_th" + str(thread_id) + "] Arrêté !" )
    return
