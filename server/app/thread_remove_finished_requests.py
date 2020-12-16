#!/usr/bin/python3
# coding: utf-8

from time import time

try :
    from wait_until import wait_until
except ModuleNotFoundError :
    from .wait_until import wait_until


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Suppression des anciennes requêtes terminées des objets Scan_Requests_Pipeline
et User_Requests_Pipeline.
"""
def thread_remove_finished_requests( thread_id : int, shared_memory ) :
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_user_requests = shared_memory.user_requests
    shared_memory_scan_requests = shared_memory.scan_requests
    shared_memory_http_limitator = shared_memory.http_limitator
    
    # Fonction à passer à "wait_until()"
    # Passer "shared_memory.keep_running" ne fonctionne pas
    def break_wait() : return not shared_memory.keep_service_alive
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        # On dort dix minutes = 600 secondes
        end_sleep_time = time() + 600
        if not wait_until( end_sleep_time, break_wait ) :
            break # Le serveur doit s'arrêter
        
        print( f"[remove_finished_th{thread_id}] Délestage des anciennes requêtes..." )
        
        # Pipeline des requêtes utilisateurs
        shared_memory_user_requests.shed_requests()
        
        # Pipeline des requêtes de scan
        shared_memory_scan_requests.shed_requests()
        
        # Limitateur de requêtes HTTP sur l'API
        shared_memory_http_limitator.reset()
    
    print( f"[remove_finished_th{thread_id}] Arrêté !" )
    return
