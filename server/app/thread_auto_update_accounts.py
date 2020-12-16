#!/usr/bin/python3
# coding: utf-8

import datetime
from time import time

try :
    from wait_until import wait_until
except ModuleNotFoundError :
    from .wait_until import wait_until

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from tweet_finder.database import SQLite_or_MySQL
from tweet_finder.twitter import TweepyAbstraction


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Mise à jour automatique des comptes dans la base de données.
Permet de gagner du temps lors d'une requête.
"""
def thread_auto_update_accounts( thread_id : int, shared_memory ) :
    # Accès direct à la base de données
    bdd_direct_access = SQLite_or_MySQL()
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    twitter = TweepyAbstraction( param.API_KEY,
                                param.API_SECRET,
                                param.OAUTH_TOKEN,
                                param.OAUTH_TOKEN_SECRET )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_scan_requests = shared_memory.scan_requests
    
    # Période de mise à jour automatique des comptes
    update_period = datetime.timedelta( days = param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE )
    
    # Fonction à passer à "wait_until()"
    # Passer "shared_memory.keep_running" ne fonctionne pas
    def break_wait() : return not shared_memory.keep_service_alive
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        # Prendre l'itérateur sur les comptes dans la base de donnée, triés
        # dans l'ordre du moins récemment mise à jour au plus récemment mis à jour
        oldest_updated_account_iterator = bdd_direct_access.get_oldest_updated_account()
        
        # Compteurs du nombre d'itération
        count = 0
        
        # oldest_updated_account[0] : L'ID du compte Twitter
        # oldest_updated_account[1] : Sa date de dernière MàJ avec l'API de recherche
        # oldest_updated_account[2] : Sa date dernière MàJ avec l'API de timeline
        for oldest_updated_account in oldest_updated_account_iterator  :
            count += 1
            
            # Vérifier quand même qu'il ne faut pas s'arrêter
            if not shared_memory.keep_service_alive :
                break
            
            # Vérifier que le compte n'est pas déjà en cours d'indexation
            if shared_memory_scan_requests.get_request( oldest_updated_account[0] ) != None :
                continue
            
            # Prendre la date actuelle
            now = datetime.datetime.now()
            
            # Si une des deux dates est à NULL, on force le scan
            if oldest_updated_account[1] == None or oldest_updated_account[2] == None :
               pass
            
            # Sinon, on prendre la date minimale
            else :
                min_date = min( oldest_updated_account[1], oldest_updated_account[2] )
                
                # Si cette mise à jour est à moins de
                # param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE jours d'aujourd'hui,
                # il faut attendre
                if now - min_date < update_period :
                    # Reprise dans (update_period - (now - min_date))
                    wait_time = int( (update_period - (now - min_date)).total_seconds() )
                    end_sleep_time = time() + wait_time
                    
                    print( f"[auto_update_th{thread_id}] Reprise dans {wait_time} secondes, pour lancer le scan du compte ID {oldest_updated_account[0]}." )
                    
                    # Si la boucle d'attente a été cassée, c'est que le serveur
                    # doit s'arrêter, il faut retourner à la boucle
                    # "while shared_memory.keep_service_alive"
                    if not wait_until( end_sleep_time, break_wait ) :
                        break
                    
                    # Si le temps d'attente est bien arrivé au bout, on peut
                    # MàJ le compte. Pas besoin de reboucler sur l'itérateur,
                    # puisque les seules modifications sur l'ordre des comptes
                    # dans la BDD peuvent être des MàJ plus récente, c'est à
                    # dire nos modifications, et ce thread est unique (Ou bien
                    # des nouveaux comptes)
                    # L'itérateur se terminera donc naturellement
            
            # On cherche le nom du compte Twitter
            account_name = twitter.get_account_id( oldest_updated_account[0], invert_mode = True )
            
            # Si l'ID du compte Twitter n'existe plus
            if account_name == None :
                print( f"[auto_update_th{thread_id}] L'ID de compte Twitter {oldest_updated_account[0]} n'est plus accessible ou n'existe plus !" )
                
                # On met la date locale de la dernière MàJ à aujourd'hui pour
                # éviter de ré-avoir cet ID à la prochaine itération
                # On peut faire ce INSERT INTO, pusiqu'il n'y a que ce thread qui
                # utilise la date locale de dernière MàJ, et que ce thread est
                # unique
                bdd_direct_access.set_account_SearchAPI_last_tweet_date( oldest_updated_account[0],
                                                                         bdd_direct_access.get_account_SearchAPI_last_tweet_date( oldest_updated_account[0] ) )
                bdd_direct_access.set_account_TimelineAPI_last_tweet_id( oldest_updated_account[0],
                                                                         bdd_direct_access.get_account_TimelineAPI_last_tweet_id( oldest_updated_account[0] ) )
            
            # Sinon, on lance le scan pour ce compte
            else :
                print( f"[auto_update_th{thread_id}] Mise à jour du compte @{account_name} (ID {oldest_updated_account[0]})." )
                shared_memory_scan_requests.launch_request( oldest_updated_account[0],
                                                            account_name,
                                                            is_prioritary = False )
        
        # Si il n'y avait aucun compte dans l'itérateur
        if count == 0 :
            print( f"[auto_update_th{thread_id}] La base de données n'a pas de comptes Twitter enregistré !" )
            
            # Retest dans une heure = 3600 secondes
            end_sleep_time = time() + 3600
            wait_until( end_sleep_time, break_wait )
    
    print( f"[auto_update_th{thread_id}] Arrêté !" )
    return
