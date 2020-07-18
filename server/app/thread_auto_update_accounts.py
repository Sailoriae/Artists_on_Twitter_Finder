#!/usr/bin/python3
# coding: utf-8

import datetime
from time import sleep

try :
    from class_Request import Request
except ModuleNotFoundError :
    from .class_Request import Request

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from tweet_finder.database import SQLite_or_MySQL


"""
Mise à jour automatique des comptes dans la base de données.
Permet de gagner du temps lors d'une requête.
"""
def thread_auto_update_accounts( thread_id : int, pipeline ) :
    # Accès direct à la base de données
    bdd_direct_access = SQLite_or_MySQL()
    
    # Tant que on ne nous dit pas de nous arrêter
    while pipeline.keep_service_alive :
        # Prendre le compte avec la mise à jour la plus vielle
        oldest_updated_account = bdd_direct_access.get_oldest_updated_account()
        
        if oldest_updated_account == None :
            print( "[auto_update_th" + str(thread_id) + "] La base de données n'a pas de comptes Twitter enregistrés !" )
            # Retest dans une heure (1200*3 = 3600)
            for i in range( 1200 ) :
                sleep( 3 )
                if not pipeline.keep_service_alive :
                    break
            continue
        
        # Vérifier que le compte n'est pas déjà en cours d'indexation
        if pipeline.check_is_indexing( oldest_updated_account[0] ) :
            # On reprend dans 5 minutes (200*3 = 600)
            for i in range( 200 ) :
                sleep( 3 )
                if not pipeline.keep_service_alive :
                    break
            continue
        
        # Prendre la date actuelle
        now = datetime.datetime.now()
        
        # Prendre la date minimale
        if oldest_updated_account[1] == None :
            min_date = oldest_updated_account[2]
        elif oldest_updated_account[2] == None :
            min_date = oldest_updated_account[1]
        else :
            min_date = min( oldest_updated_account[1], oldest_updated_account[2] )
        
        # Si cette mise à jour est à moins de
        # param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE jours d'aujourd'hui, ça ne
        # sert à rien de MàJ
        if now - min_date < datetime.timedelta( days = param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE ) :
            # Retest dans (now - min_date) en secondes
            for i in range( int( (now - min_date).total_seconds() / 3 ) ) :
                sleep( 3 )
                if not pipeline.keep_service_alive :
                    break
            continue
        
        # On lance le scan pour ce compte
        result = pipeline.launch_index_or_update_only( account_id = oldest_updated_account[0] )
        
        # Si l'ID du compte Twitter n'existe plus
        if result == False :
            print( "[auto_update_th" + str(thread_id) + "] L'ID de compte Twitter " + str(oldest_updated_account[0]) + " n'existe plus !" )
            
            # On met la date locale de la dernière MàJ à aujourd'hui pour
            # éviter de ré-avoir cet ID à la prochaine itération
            # On peut faire ce INSERT INTO, pusiqu'il n'y a que ce thread qui
            # utilise la date locale de dernière MàK
            bdd_direct_access.set_account_last_scan( oldest_updated_account[0],
                                                     bdd_direct_access.get_account_last_scan( oldest_updated_account[0] ) )
            bdd_direct_access.set_account_last_scan_with_TwitterAPI( oldest_updated_account[0],
                                                                     bdd_direct_access.get_account_last_scan_with_TwitterAPI( oldest_updated_account[0] ) )
        
        else :
            print( "[auto_update_th" + str(thread_id) + "] Mise à jour du compte Twitter avec l'ID " + str(oldest_updated_account[0]) + "." )
        
        # On reprend dans 5 minutes (200*3 = 600)
        for i in range( 200 ) :
            sleep( 3 )
            if not pipeline.keep_service_alive :
                break
    
    print( "[auto_update_th" + str(thread_id) + "] Arrêté !" )
    return
