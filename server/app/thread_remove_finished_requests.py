#!/usr/bin/python3
# coding: utf-8

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
        
        print( "[remove_finished_th" + str(thread_id) + "] Délestage des anciennes requêtes..." )
        
        # Pipeline des requêtes utilisateurs
        shared_memory.user_requests.shed_requests()
        
        # Pipeline des requêtes de scan
        shared_memory.scan_requests.shed_requests()
        
        # Limitateur de requêtes HTTP sur l'API
        shared_memory.http_limitator.reset()
    
    print( "[remove_finished_th" + str(thread_id) + "] Arrêté !" )
    return
