#!/usr/bin/python3
# coding: utf-8

import datetime
from time import time

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( ".." )

from app.wait_until import wait_until
import parameters as param
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Mise à jour automatique des comptes dans la base de données.
Permet de gagner du temps lors d'une requête.
"""
def thread_auto_update_accounts( thread_id : int, shared_memory ) :
    # Sécurité, vérifier que le thread est unique
    if thread_id != 1 :
        raise RuntimeError( "Ce thread doit être unique, et doit pas conséquent avoir 1 comme identifiant (\"thread_id\") !" )
    
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
    update_period = datetime.timedelta( days = param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE ).total_seconds()
    
    # Fonction à passer à "wait_until()"
    # Passer "shared_memory.keep_running" ne fonctionne pas
    def break_wait() : return not shared_memory.keep_service_alive
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        # Si il n'y a aucun compte dans la base de données
        if shared_memory.accounts_count < 1 :
            print( f"[auto_update_th{thread_id}] La base de données n'a pas de comptes Twitter enregistré !" )
            
            # Retest dans une heure = 3600 secondes
            end_sleep_time = time() + 3600
            wait_until( end_sleep_time, break_wait )
            continue
        
        # Instant juste avant le lancement d'une mise à jour
        # Sert à être précis pour répartir les mises à jour
        start = datetime.datetime.now()
        
        # Calculer la moyenne du temps entre chaque mise à jour
        # Sert à répartier les mises à jour
        # Pas besoin de le MàJ dans la boucle "for", car l'itérateur est un
        # instantané des comptes dans la BDD
        max_wait = update_period / shared_memory.accounts_count
        
        # Prendre l'itérateur sur les comptes dans la base de donnée, triés
        # dans l'ordre du moins récemment mise à jour au plus récemment mis à jour
        oldest_updated_account_iterator = bdd_direct_access.get_oldest_updated_account()
        
        # oldest_updated_account[0] : L'ID du compte Twitter
        # oldest_updated_account[1] : Sa date de dernière MàJ avec l'API de recherche
        # oldest_updated_account[2] : Sa date dernière MàJ avec l'API de timeline
        for oldest_updated_account in oldest_updated_account_iterator  :
            # Vérifier quand même qu'il ne faut pas s'arrêter
            if not shared_memory.keep_service_alive :
                break
            
            # Vérifier que le compte n'est pas déjà en cours d'indexation
            if shared_memory_scan_requests.get_request( oldest_updated_account[0] ) != None :
                continue
            
            # Si une des deux dates est à NULL, on force le scan
            if oldest_updated_account[1] == None or oldest_updated_account[2] == None :
               pass
            
            # Sinon, on prendre la date minimale
            else :
                min_date = min( oldest_updated_account[1], oldest_updated_account[2] )
                
                # Calculer le temps écoulé entre la dernière MàJ et maintenant
                diff = (start - min_date).total_seconds()
                
                # Si cette mise à jour est à moins de
                # param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE jours d'aujourd'hui,
                # il faut attendre
                if diff < update_period :
                    # Reprise dans (update_period - (now - min_date))
                    wait_time = update_period - diff
                    
                    # Prendre de l'avance : Le temps d'attente maximal est
                    # le temps moyen entre deux MàJ, c'est à dire la période
                    # de MàJ divisée par le nombre de comptes dans la BDD
                    # Cela permet de répartir les MàJ et d'éviter de créer des
                    # pics de charge sur le serveur
                    if wait_time > max_wait :
                        wait_time = max_wait
                    
                    end_sleep_time = time() + wait_time
                    
                    print( f"[auto_update_th{thread_id}] Reprise dans {int(wait_time)} secondes, pour lancer le scan du compte ID {oldest_updated_account[0]}." )
                    
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
            
            # Prendre l'instant juste avant la MàJ (Prend aussi l'appel à l'API
            # Twitter qui est une requête HTTP donc longue)
            start = datetime.datetime.now()
            
            # Comme on va jusqu'au bout de l'itérateur, on vérifie que la date
            # de MàJ de ce compte n'ait pas changé dans la base de données,
            # c'est à dire qu'il y a eu une requête de scan lancée
            # On le fait seulement maintenant, et pas avant la boucle d'attente
            # car la répartition des MàJ avec  un temps minimal nous ferait
            # prendre trop d'avance
            if ( bdd_direct_access.get_account_SearchAPI_last_scan_local_date( oldest_updated_account[0] ) != oldest_updated_account[1] and
                 bdd_direct_access.get_account_TimelineAPI_last_scan_local_date( oldest_updated_account[0] ) != oldest_updated_account[2] ) :
                print( f"[auto_update_th{thread_id}] Le compte ID {oldest_updated_account[0]} a eu un scan provoqué par un utilisateur, on peut le sauter." )
                
                # On peut sauter ce compte, on le reverra la prochaine fois
                # qu'on lancera l'itérateur
                continue
            
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
    
    print( f"[auto_update_th{thread_id}] Arrêté !" )
    return
