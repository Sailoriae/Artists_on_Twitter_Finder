#!/usr/bin/python3
# coding: utf-8

import datetime
from time import sleep


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Suppression des anciennes requêtes terminées de l'objet Pipeline.
"""
def thread_remove_finished_requests( thread_id : int, pipeline ) :
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        # On dors une heure (1200*3 = 3600)
        for i in range( 1200 ) :
            sleep( 3 )
            if not pipeline.keep_service_alive :
                break
        
        # On bloque l'accès la liste des requêtes du Pipeline
        pipeline.requests_sem.acquire()
        
        # On prend la date actuelle
        now = datetime.datetime.now()
        
        # On filtre la liste des requêtes
        new_requests_list = []
        for request in pipeline.requests :
            if request.finished_date != None :
                # Si la date de fin est à moins de 24h de maintenant, on garde
                # cette requête
                if now - request.finished_date < datetime.timedelta( hours = 24 ) :
                    new_requests_list.append( request )
        
        # On installe la nouvelle liste
        pipeline.requests = new_requests_list
        
        # On débloque l'accès à la liste des requêtes du Pipeline
        pipeline.requests_sem.release()
    
    print( "[remove_finished_th" + str(thread_id) + "] Arrêté !" )
    return
