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
        # On dors dix minutes (200*3 = 600 secondes = 10 minutes)
        for i in range( 200 ) :
            sleep( 3 )
            if not shared_memory.keep_service_alive :
                break
        
        # On prend la date actuelle
        now = datetime.datetime.now()
        
        # ====================================================================
        # Pipeline des requêtes utilisateurs
        # ====================================================================
        
        # On bloque l'accès la liste des requêtes du Pipeline des requêtes
        # utilisateurs
        shared_memory.user_requests.requests_sem.acquire()
        
        # On filtre la liste des requêtes utilisateurs
        new_requests_list = []
        for request in shared_memory.user_requests.requests :
            if request.finished_date != None :
                # Si la date de fin est à moins de 3 heures de maintenant, on
                # peut peut-être garder cette requête
                if now - request.finished_date < datetime.timedelta( hours = 3 ) :
                    # Si la requête s'est terminée en erreur
                    if request.problem != None :
                        # Si l'URL de requête est invalide ou le site n'est pas
                        # supporté, on garde la requête 10 minutes
                        if request.problem in [ "INVALID_URL",
                                                "UNSUPPORTED_WEBSITE"] :
                            if now - request.finished_date < datetime.timedelta( minutes = 10 ) :
                                new_requests_list.append( request )
                        # Sinon, on la garde 1 heure
                        else :
                            if now - request.finished_date < datetime.timedelta( hours = 1 ) :
                                new_requests_list.append( request )
                    # Si la requête ne s'est pas terminée en erreur, on la
                    # garde 3 heures
                    else :
                        new_requests_list.append( request )
        
        # On installe la nouvelle liste
        shared_memory.user_requests.requests = new_requests_list
        
        # On débloque l'accès à la liste des requêtes du Pipeline des requêtes
        # utilisateurs
        shared_memory.user_requests.requests_sem.release()
        
        # ====================================================================
        # Pipeline des requêtes de scan
        # ====================================================================
        
        # On bloque l'accès la liste des requêtes du Pipeline des requêtes de
        # scan
        shared_memory.scan_requests.requests_sem.acquire()
        
        # On filtre la liste des requêtes de scan
        new_requests_list = []
        for request in shared_memory.scan_requests.requests :
            if request.finished_date != None :
                # Si la date de fin est à moins de 24h de maintenant, on garde
                # cette requête
                if now - request.finished_date < datetime.timedelta( hours = 24 ) :
                    new_requests_list.append( request )
        
        # On installe la nouvelle liste
        shared_memory.scan_requests.requests = new_requests_list
        
        # On débloque l'accès à la liste des requêtes du Pipeline des requêtes
        # de scan
        shared_memory.scan_requests.requests_sem.release()
        
        # ====================================================================
        # Limitateur de requêtes HTTP sur l'API
        # ====================================================================
        
        # On vide le dictionnaire de la date du dernier appel par adresse IP
        shared_memory.http_limitator.reset()
    
    print( "[remove_finished_th" + str(thread_id) + "] Arrêté !" )
    return
