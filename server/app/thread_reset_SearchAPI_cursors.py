#!/usr/bin/python3
# coding: utf-8

import datetime
from time import sleep, time

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from tweet_finder.database import SQLite_or_MySQL


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Le moteur de recherche de Twitter fluctue, et est assez mal documenté. Certains
Tweets peuvent être désindexés ou réindexés.
Il est donc intéressant de temps en temps de réintialiser le curseur
d'indexation avec l'API de recherche pour chaque compte.
Cela ne supprime ou ne réindexe aucun Tweet dans la base ! On en ajoute juste.
La vitesse dépend donc essentiellement du thread de listage.
"""
def thread_reset_SearchAPI_cursors( thread_id : int, shared_memory ) :
    # Accès direct à la base de données
    bdd_direct_access = SQLite_or_MySQL()
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_scan_requests = shared_memory.scan_requests
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        # Prendre l'itérateur sur les comptes dans la base de donnée, triés
        # dans l'ordre du moins récemment reset au plus récemment reset
        oldest_reseted_account_iterator = bdd_direct_access.get_oldest_reseted_account()
        
        # Prendre la date actuelle
        now = datetime.datetime.now()
        
        # Période de reset des curseurs d'indexation avec l'API de recherche
        reset_period = datetime.timedelta( days = param.RESET_SEARCHAPI_CURSORS_PERIOD )
        
        # Mis à True si on a sauté le reset d'un compte qui était déjà en cours
        # d'indexation
        already_indexing_account = False
        
        # Pour chaque compte dans la BDD
        for account in oldest_reseted_account_iterator :
            # Si on est arrivé au compte reset il y a moins que la période
            if account["last_cursor_reset_date"] != None and now - account["last_cursor_reset_date"] < reset_period :
                # Reprise dans (reset_period - (now - account["last_cursor_reset_date"]))
                wait_time = int( (reset_period - (now - account["last_cursor_reset_date"])).total_seconds() )
                
                # Si on a sauté le reset d'un compte qui était déjà en cours
                # d'indexation, on dort au maximum 24h = 86400 secondes
                if already_indexing_account and wait_time > 86400 :
                    wait_time = 86400
                
                end_sleep_time = time() + wait_time
                
                print( f"[reset_cursors_th{thread_id}] Reprise dans {wait_time} secondes, pour reset le curseur d'indexation avec l'API de recherche du compte ID {account['account_id']}." )
                while True :
                    sleep( 3 )
                    if time() > end_sleep_time :
                        break
                    if not shared_memory.keep_service_alive :
                        break
                # Recommencer la boucle du "keep_service_alive"
                break # Arrêt de l'itération "for"
            
            # Vérifier que le compte n'est pas déjà en cours d'indexation
            if shared_memory_scan_requests.get_request( account["account_id"] ) != None :
                already_indexing_account = True
                continue # On le passe, il y retournera dans 24h
            
            # On peut reset son curseur
            # Cela reset aussi sa date locale de dernière MàJ
            bdd_direct_access.reset_account_SearchAPI_last_tweet_date( account["account_id"] )
            
            # Dire au thread de MàJ auto qu'il peut reboucler car on a reset
            # le curseur d'indexation d'un compte
            # Car c'est lui qui se chargera de lancer la MàJ du compte
            shared_memory.force_auto_update_reloop = True
    
    print( f"[reset_cursors_th{thread_id}] Arrêté !" )
    return
