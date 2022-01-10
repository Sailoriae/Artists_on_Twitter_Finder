#!/usr/bin/python3
# coding: utf-8

import datetime
from time import time
import queue

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    from os import getcwd as get_wdir
    from sys import path
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( "../.." )
    path.append(get_wdir())

from threads.maintenance.wait_until import wait_until
import parameters as param
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Le moteur de recherche de Twitter fluctue, et est assez mal documenté. Certains
Tweets peuvent être désindexés ou réindexés.
Il est donc intéressant de temps en temps de réintialiser le curseur
d'indexation avec l'API de recherche pour chaque compte.
Cela ne supprime ou ne réindexe aucun Tweet dans la base ! On en ajoute juste.
La vitesse dépend donc essentiellement du thread de listage.

Un autre intérêt de ce thread est qu'il permet de réindexer des comptes qui
auraient changé de nom (@nom) durant son listage. Car le listage des Tweets
sur l'API de recherche ne peut se faire qu'avec le nom du compte, alors que
AOTF indexe les Tweets avec les ID de comptes. Ce scénario est cependant très
peu probable.
"""
def thread_reset_SearchAPI_cursors( thread_id : int, shared_memory ) :
    # Sécurité, vérifier que le thread est unique
    if thread_id != 1 :
        raise AssertionError( "Ce thread doit être unique, et doit pas conséquent avoir 1 comme identifiant (\"thread_id\") !" )
    
    # Accès direct à la base de données
    bdd = SQLite_or_MySQL()
    
    # Initialisation de notre couche d'abstraction à l'API Twitter
    twitter = TweepyAbstraction( param.API_KEY,
                                 param.API_SECRET,
                                 param.OAUTH_TOKEN,
                                 param.OAUTH_TOKEN_SECRET )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_scan_requests = shared_memory.scan_requests
    
    # Période de reset des curseurs d'indexation avec l'API de recherche
    reset_period = datetime.timedelta( days = param.RESET_SEARCHAPI_CURSORS_PERIOD ).total_seconds()
    
    # File d'attente des comptes dont leur requête de scan existe déjà
    # Parce que c'est trop compliqué et risqué de bidouiller des requêtes de
    # scan pour les redémarrer partiellement
    # C'est plus simple de faire une file d'attente ici pour retester à chaque
    # itération de la boucle "for"
    to_reset_queue = queue.Queue()
    
    # Même que la file d'attente ci-dessus, mais permet d'éviter une boucle
    # infinie (Les éléments y sont mis temporairement)
    to_reset_temp_queue = queue.Queue()
    
    # Fonction à passer à "wait_until()"
    # Passer "shared_memory.keep_running" ne fonctionne pas
    def break_wait() : return not shared_memory.keep_threads_alive
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_threads_alive :
        # Si il n'y a aucun compte dans la base de données
        if shared_memory.accounts_count < 1 :
            print( f"[reset_cursors_th{thread_id}] La base de données n'a pas de comptes Twitter enregistré !" )
            
            # Retest dans une heure = 3600 secondes
            end_sleep_time = time() + 3600
            wait_until( end_sleep_time, break_wait )
        
        # Instant juste avant le lancement d'une mise à jour
        # Sert à être précis pour répartir les mises à jour
        start = datetime.datetime.now()
        
        # Prendre l'itérateur sur les comptes dans la base de donnée, triés
        # dans l'ordre du moins récemment reset au plus récemment reset
        oldest_reseted_account_iterator = bdd.get_oldest_reseted_account()
        
        # Pour chaque compte dans la BDD
        for account in oldest_reseted_account_iterator :
            # Vérifier quand même qu'il ne faut pas s'arrêter
            if not shared_memory.keep_threads_alive :
                break
            
            # Vérifier que le compte ait bien terminé sa première indexation
            # Sinon, on le passe, c'est au thread de MàJ auto de s'en charger
            if account["last_SearchAPI_indexing_local_date"] == None :
                continue
            
            # Calculer le temps écoulé entre le dernier reset et maintenant
            try :
                diff = (start - account["last_cursor_reset_date"]).total_seconds()
            
            # Si le compte n'a pas de date de dernier reset, c'est pas normal,
            # donc on solutionne ce problème en l'égalisant avec la date du
            # curseur d'indexation
            except TypeError as error :
                 print( f"[reset_cursors_th{thread_id}] Le compte ID {account['account_id']} n'a pas de date de dernier reset de son curseur d'indexation. Pourtant il a une date de dernière indexation avec l'API de recherche, c'est pas normal. On égalise ces deux dates." )
                 print( error )
                 bdd.equalize_reset_account_SearchAPI_date( account['account_id'] )
                 continue # On ne force pas le reset, ça ne sert à rien
            
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
                max_wait = reset_period / shared_memory.accounts_count
                if wait_time > max_wait :
                    wait_time = max_wait
                
                end_sleep_time = time() + wait_time
                
                print( f"[reset_cursors_th{thread_id}] Reprise dans {int(wait_time)} secondes, pour reset le curseur d'indexation avec l'API de recherche du compte ID {account['account_id']}." )
                
                # Si la boucle d'attente a été cassée, c'est que le serveur
                # doit s'arrêter, il faut retourner à la boucle
                # "while shared_memory.keep_threads_alive"
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
            bdd.reset_account_SearchAPI_last_tweet_date( account["account_id"] )
            
            # Si l'ID du compte Twitter n'existe plus, on le laisse tel quel,
            # avec son curseur reset
            if account_name == None :
                print( f"[reset_cursors_th{thread_id}] L'ID de compte Twitter {account['account_id']} n'est plus accessible ou n'existe plus !" )
            
            # Sinon, on l'ajoute à la file d'attente des comptes dont il faut
            # lancer l'indexation
            else :
                print( f"[reset_cursors_th{thread_id}] Reset du curseur d'indexation avec l'API de recherche du compte @{account_name} (ID {account['account_id']}) et lancement de sa mise à jour." )
                account["account_name"] = account_name # On enregistre le nom du compte pour ne pas avoir à le re-résoudre
                account["last_try"] = 0 # Date du dernier essai dans notre file d'attente
                account["reset_time"] = time() # Date de reset du curseur
                to_reset_queue.put( account )
            
            # A chaque itération, on parcours la file d'attente des comptes
            # dont il faut reset le curseur
            while True :
                try : account = to_reset_queue.get( block = False )
                except queue.Empty : break
                
                # On réessaye de lancer une requête toutes les 24 heures
                # Attention : On ne remet pas directement dans la file
                # d'attente pour éviter un bouclage infini
                if time() - account["last_try"] <= 86400 :
                    to_reset_temp_queue.put( account )
                    continue
                account["last_try"] = time()
                
                # Lancer une nouvelle requête de scan pour ce compte, permet de
                # voir si la requête d'indexation de ce compte n'existe pas déjà
                request = shared_memory_scan_requests.launch_request( account['account_id'],
                                                                      account_name,
                                                                      is_prioritary = False )
                
                # Si la requête est plus jeune que le reset du curseur, c'est
                # que nous ou quelqu'un d'autre l'a lancée, mais elle a pris
                # on prendra le curseur reset
                # Donc on peut laisser ce compte tranquille
                if request.start > account["reset_time"] :
                    continue
                
                # Si la requête a commencé le listage avec l'API de recherche
                # on remet le compte dans notre file d'attente
                # Attention : On ne remet pas directement dans la file
                # d'attente pour éviter un bouclage infini
                if request.started_SearchAPI_listing :
                    to_reset_temp_queue.put( account )
                
                # Sinon, on peut laisser ce compte tranquille, le listage
                # prendra bien le curseur reset
            
            # Vider la file temporaire dans la vraie file des comptes dont il
            # faut reset leur curseur
            while True :
                try : to_reset_queue.put( to_reset_temp_queue.get( block = False ) )
                except queue.Empty : break
    
    print( f"[reset_cursors_th{thread_id}] Arrêté !" )
    return
