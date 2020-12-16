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
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    twitter = TweepyAbstraction( param.API_KEY,
                                param.API_SECRET,
                                param.OAUTH_TOKEN,
                                param.OAUTH_TOKEN_SECRET )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_scan_requests = shared_memory.scan_requests
    
    # Période de reset des curseurs d'indexation avec l'API de recherche
    reset_period = datetime.timedelta( days = param.RESET_SEARCHAPI_CURSORS_PERIOD ).total_seconds()
    
    # Fonction à passer à "wait_until()"
    # Passer "shared_memory.keep_running" ne fonctionne pas
    def break_wait() : return not shared_memory.keep_service_alive
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        # Si il n'y a aucun compte dans la base de données
        if shared_memory.accounts_count < 1 :
            print( f"[reset_cursors_th{thread_id}] La base de données n'a pas de comptes Twitter enregistré !" )
            
            # Retest dans une heure = 3600 secondes
            end_sleep_time = time() + 3600
            wait_until( end_sleep_time, break_wait )
        
        # Instant juste avant le lancement d'une mise à jour
        # Sert à être précis pour répartir les mises à jour
        start = datetime.datetime.now()
        
        # Calculer la moyenne du temps entre chaque mise à jour
        # Sert à répartier les mises à jour
        # Pas besoin de le MàJ dans la boucle "for", car l'itérateur est un
        # instantané des comptes dans la BDD
        max_wait = reset_period / shared_memory.accounts_count
        
        # Prendre l'itérateur sur les comptes dans la base de donnée, triés
        # dans l'ordre du moins récemment reset au plus récemment reset
        oldest_reseted_account_iterator = bdd_direct_access.get_oldest_reseted_account()
        
        # Pour chaque compte dans la BDD
        for account in oldest_reseted_account_iterator :
            # Vérifier quand même qu'il ne faut pas s'arrêter
            if not shared_memory.keep_service_alive :
                break
            
            # Vérifier que le compte ait bien terminé sa première indexation
            # Sinon, on le passe, c'est au thread de MàJ auto de s'en charger
            if account["last_SearchAPI_indexing_local_date"] == None :
                continue
            
            # Calculer le temps écoulé entre le dernier reset et maintenant
            try :
                diff = (start - account["last_cursor_reset_date"]).total_seconds()
            
            # Si le compte n'a pas de date de dernier reset, déjà c'est pas
            # normal, et ensuite, on le reset forcément
            except TypeError as error :
                 print( f"[reset_cursors_th{thread_id}] Le compte ID {account['account_id']} n'a par de date de dernier reset de son curseur d'indexation. Pourtant il a une date de dernière indexation avec l'API de recherche. C'est pas normal !" )
                 print( error )
                 diff = reset_period # Forcer le reset
            
            # Si le reset du curseur de ce compte est à moins de
            # param.RESET_SEARCHAPI_CURSORS_PERIOD jours d'aujourd'hui,
            # il faut attendre
            if diff < reset_period :
                # Reprise dans (reset_period - (now - account["last_cursor_reset_date"]))
                wait_time = reset_period - diff
                
                # Prendre de l'avance : Le temps d'attente maximal est le temps
                # moyen entre deux MàJ, c'est à dire la période de MàJ divisée
                # par le nombre de comptes dans la BDD
                # Cela permet de répartir les MàJ et d'éviter de créer des pics
                # de charge sur le serveur
                if wait_time > max_wait :
                    wait_time = max_wait
                
                end_sleep_time = time() + wait_time
                
                print( f"[reset_cursors_th{thread_id}] Reprise dans {int(wait_time)} secondes, pour reset le curseur d'indexation avec l'API de recherche du compte ID {account['account_id']}." )
                
                # Si la boucle d'attente a été cassée, c'est que le serveur
                # doit s'arrêter, il faut retourner à la boucle
                # "while shared_memory.keep_service_alive"
                if not wait_until( end_sleep_time, break_wait ) :
                    break
                
                # Si le temps d'attente est bien arrivé au bout, on peut reset
                # le curseur du compte. Pas besoin de reboucler sur l'itérateur,
                # puisque les seules modifications sur l'ordre des comptes dans
                # la BDD peuvent être des reset plus récent, c'est à dire nos
                # modifications, et ce thread est unique (Ou bien des nouveaux
                # comptes)
                # L'itérateur se terminera donc naturellement
            
            # Prendre l'instant juste avant la MàJ (Prend aussi l'appel à l'API
            # Twitter qui est une requête HTTP donc longue)
            start = datetime.datetime.now()
            
            # On cherche le nom du compte Twitter
            account_name = twitter.get_account_id( account["account_id"], invert_mode = True )
            
            # Dans tous les cas, on reset son curseur
            bdd_direct_access.reset_account_SearchAPI_last_tweet_date( account["account_id"] )
            
            # Si l'ID du compte Twitter n'existe plus, on le laisse tel quel,
            # avec son curseur reset
            if account_name == None :
                print( f"[reset_cursors_th{thread_id}] L'ID de compte Twitter {account['account_id']} n'est plus accessible ou n'existe plus !" )
            
            # Sinon, on FORCE l'indexation pour ce compte
            else :
                print( f"[reset_cursors_th{thread_id}] Reset du curseur d'indexation avec l'API de recherche du compte @{account_name} (ID {account['account_id']}) et lancement de sa mise à jour." )
                
                shared_memory_scan_requests.launch_request( account['account_id'],
                                                            account_name,
                                                            is_prioritary = False,
                                                            force_launch = True )
    
    print( f"[reset_cursors_th{thread_id}] Arrêté !" )
    return
