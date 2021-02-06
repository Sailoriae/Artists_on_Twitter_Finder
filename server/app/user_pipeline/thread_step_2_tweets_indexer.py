#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep, time
from dateutil.tz import tzlocal, UTC
import datetime

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
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

import parameters as param
from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
from shared_memory.open_proxy import open_proxy


"""
ETAPE 2 du traitement d'une requête.
Thread de lancement de l'indexation ou de la mise à jour de l'indexation des
Tweets des comptes Twitter trouvés et validés par l'étape précédente.
Lance dans le pipeline de traitement des requêtes d'indexation, et surveille
l'état des requêtes qu'il a lancé.
"""
def thread_step_2_tweets_indexer( thread_id : int, shared_memory ) :
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_threads_registry = shared_memory.threads_registry
    shared_memory_user_requests = shared_memory.user_requests
    shared_memory_scan_requests = shared_memory.scan_requests
    shared_memory_user_requests_step_2_tweets_indexer_queue = shared_memory_user_requests.step_2_tweets_indexer_queue
    shared_memory_user_requests_thread_step_2_tweets_indexer_sem = shared_memory_user_requests.thread_step_2_tweets_indexer_sem
    
    # Dire qu'on ne fait rien
    shared_memory_threads_registry.set_request( f"thread_step_2_tweets_indexer_th{thread_id}", None )
    
    # Timezone locale
    local_tz = tzlocal()
    
    # Accès direct à la base de données
    # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
    bdd_direct_access = SQLite_or_MySQL()
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = shared_memory_user_requests_step_2_tweets_indexer_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_2_tweets_indexer_th{thread_id}", request )
        
        # Si on a vu cette requête il y a moins de 5 secondes, c'est qu'il n'y
        # a pas beaucoup de requêtes dans le pipeline, on peut donc dormir
        # 3 secondes, pour éviter de trop itérer dessus
        if time() - request.last_seen_indexer < 5 :
            sleep( 3 )
        request.last_seen_indexer = time()
        
        # Si la requête n'a pas eu les scans de ses comptes Twitter lancés,
        # c'est que c'est la première fois qu'on la voit
        if request.scan_requests == None :
            request.scan_requests = []
            
            # Sémaphore pour être bien tout seul dans cette procédure assez
            # particulière
            shared_memory_user_requests_thread_step_2_tweets_indexer_sem.acquire()
            
            # On passe la requête à l'étape suivante, c'est à dire notre étape
            shared_memory_user_requests.set_request_to_next_step( request )
            
            # Pour chaque compte de la liste des comptes Twitter trouvé
            for (account_name, account_id) in request.twitter_accounts_with_id :
                
                # On prend ses deux dernières dates de scan
                last_scan_1 = bdd_direct_access.get_account_SearchAPI_last_scan_local_date( account_id )
                last_scan_2 = bdd_direct_access.get_account_TimelineAPI_last_scan_local_date( account_id )
                
                # Si l'une des deux est à NULL, il faut scanner, ou se
                # rattacher au scan du compte déjà en cours
                if last_scan_1 == None or last_scan_2 == None :
                    print( f"[step_2_th{thread_id}] @{account_name} n'est pas dans la base de données ! On lance une nouvelle requête de scan ou on suit celle déjà en cours pour ce compte !" )
                    
                    # launch_request() va soit nous retourner la requête de
                    # scan en cours, soit en créer une nouvelle
                    # Si la requête déjà existante n'était pas prioritaire, elle
                    # va la passer en prioritaire
                    scan_request = shared_memory_scan_requests.launch_request( account_id,
                                                                               account_name,
                                                                               is_prioritary = True )
                    
                    # On suit la progression de cette requête
                    request.scan_requests += [ scan_request.get_URI() ] # Ne peut pas faire de append avec Pyro
                    
                    # Forcer la fermeture du proxy
                    scan_request.release_proxy()
                    
                    # On indique qu'on a des indexations pour la première fois
                    request.has_first_time_scan = True
                
                # Sinon, on prendre la date minimale
                else :
                    min_date = min( last_scan_1, last_scan_2 )
                    
                    # On a besoin de mettre le fuseau horaire dans la
                    # date minimale
                    min_date = min_date.replace( tzinfo = local_tz )
                    
                    # Si la date de l'image de requête n'a pas d'info sur sa
                    # timezone, on la met en UTC
                    if request.datetime.tzinfo == None :
                        request.datetime = request.datetime.replace( tzinfo = UTC )
                    
                    # Si cette mise à jour moins 3 jours est plus
                    # vielle que la date de l'illustration, il faut MàJ
                    # (On laisse 3 jours de marge à l'artiste pour
                    # publier sur Twitter)
                    if min_date - datetime.timedelta( days = 3 ) < request.datetime :
                        print( f"[step_2_th{thread_id}] @{account_name} est déjà dans la BDD, mais il faut le MàJ car l'illustration de requête est trop récente !" )
                        
                        scan_request = shared_memory_scan_requests.launch_request( account_id,
                                                                               account_name,
                                                                               is_prioritary = True )
                        
                        # On suit la progression de cette requête
                        request.scan_requests += [ scan_request.get_URI() ] # Ne peut pas faire de append avec Pyro
                        
                        # Forcer la fermeture du proxy
                        scan_request.release_proxy()
                    
                    else :
                        print( f"[step_2_th{thread_id}] @{account_name} est déjà dans la BDD, et on peut sauter son scan !" )
            
            # Libérer le sémaphore
            shared_memory_user_requests_thread_step_2_tweets_indexer_sem.release()
        
        # Sinon, on vérifie l'état de l'avancement des requêtes qu'on a lancé
        check_list = []
        double_continue = False # Pour faire l'équivalent de deux instruction "continue"
        for scan_request_uri in request.scan_requests :
            scan_request = open_proxy( scan_request_uri )
            check_list.append( scan_request.finished_SearchAPI_indexing and scan_request.finished_TimelineAPI_indexing )
            
            # On vérifie que le scan se passe bien ou s'est bien passé, et si
            # un thread de traitement a planté avec la requête, on l'indique
            if scan_request.has_failed :
                # Si c'est parce que tous les comptes pour scanner sont bloqués
                if len( scan_request.blocks_list ) >= len( param.TWITTER_API_KEYS ) :
                    request.problem = "BLOCKED_BY_TWITTER_ACCOUNT"
                else :
                    request.problem = "PROCESSING_ERROR"
                
                # On abandonne le processus de traitement de cette requête,
                # même si peut-être qu'on pourrait quand même rechercher
                shared_memory_user_requests.set_request_to_next_step( request, force_end = True )
                double_continue = True
                continue
            
            # Forcer la fermeture du proxy
            scan_request.release_proxy()
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_2_tweets_indexer_th{thread_id}", None )
        
        # Si l'une des requêtes de scan a eu un problème, on arrête tout avec
        # cette requête utilisateur
        if double_continue :
            request.release_proxy()
            continue
        
        # Si toutes nos requêtes ne sont pas finies, on remet la requête en
        # haut de NOTRE file d'attente
        if not all( check_list ) :
            shared_memory_user_requests_step_2_tweets_indexer_queue.put( request )
            request.release_proxy()
            continue
        
        # Sinon, on peut vider la liste des requêtes de scan
        request.scan_requests = []
        
        # Et on passe la requête à l'étape suivante
        # C'est la procédure shared_memory_user_requests.set_request_to_next_step
        # qui vérifie si elle peut
        shared_memory_user_requests.set_request_to_next_step( request )
        
        # Forcer la fermeture du proxy
        request.release_proxy()
    
    print( f"[step_2_th{thread_id}] Arrêté !" )
    return
