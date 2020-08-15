#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep, time
from dateutil.tz import tzlocal, UTC
import datetime
import Pyro4

# Ajouter le répertoire parent du répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

from tweet_finder.database import SQLite_or_MySQL


"""
ETAPE 2 du traitement d'une requête.
Thread de lancement de l'indexation ou de la mise à jour de l'indexation des
Tweets des comptes Twitter trouvés et validés par l'étape précédente.
Lance dans le pipeline de traitement des requêtes d'indexation, et surveille
l'état des requêtes qu'il a lancé.
"""
def thread_step_2_tweets_indexer( thread_id : int, shared_memory ) :
    # Dire qu'on ne fait rien
    shared_memory.user_requests.requests_in_thread.set_request( "thread_step_2_tweets_indexer_number" + str(thread_id), None )
    
    # Timezone locale
    local_tz = tzlocal()
    
    # Accès direct à la base de données
    # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
    bdd_direct_access = SQLite_or_MySQL()
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_service_alive :
        
        # On tente de sortir une requête de la file d'attente
        try :
            request = shared_memory.user_requests.step_2_tweets_indexer_queue.get( block = False )
        # Si la queue est vide, on attend une seconde et on réessaye
        except queue.Empty :
            sleep( 1 )
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_2_tweets_indexer_number" + str(thread_id), request )
        
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
            shared_memory.user_requests.thread_step_2_tweets_indexer_sem.acquire()
            
            # On passe la requête à l'étape suivante, c'est à dire notre étape
            shared_memory.user_requests.set_request_to_next_step( request )
            
            # Pour chaque compte de la liste des comptes Twitter trouvé
            for (account_name, account_id) in request.twitter_accounts_with_id :
                
                # On prend ses deux dernières dates de scan
                last_scan_1 = bdd_direct_access.get_account_GOT3_last_scan_local_date( account_id )
                last_scan_2 = bdd_direct_access.get_account_TwitterAPI_last_scan_local_date( account_id )
                
                # Si l'une des deux est à NULL, il faut scanner, ou se
                # rattacher au scan du compte déjà en cours
                if last_scan_1 == None or last_scan_2 == None :
                    print( "[step_2_th" + str(thread_id) + "] @" + account_name + " n'est pas dans la base de données ! On lance une nouvelle requête de scan ou on suit celle déjà en cours pour ce compte !" )
                    
                    # launch_request() va soit nous retourner la requête de
                    # scan en cours, soit en créer une nouvelle
                    # Si la requête déjà existante n'était pas prioritaire, elle
                    # va la passer en prioritaire
                    scan_request = shared_memory.scan_requests.launch_request( account_id,
                                                                               account_name,
                                                                               is_prioritary = True )
                    
                    # On suit la progression de cette requête
                    request.scan_requests += [ scan_request._pyroUri ] # Ne peut pas faire de append avec Pyro
                
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
                        print( "[step_2_th" + str(thread_id) + "] @" + account_name + " est déjà dans la BDD, mais il faut le MàJ car l'illustration de requête est trop récente !" )
                        
                        scan_request = shared_memory.scan_requests.launch_request( account_id,
                                                                               account_name,
                                                                               is_prioritary = True )
                        
                        # On suit la progression de cette requête
                        request.scan_requests += [ scan_request._pyroUri ] # Ne peut pas faire de append avec Pyro
                    
                    else :
                        print( "[step_2_th" + str(thread_id) + "] @" + account_name + " est déjà dans la BDD, et on peut sauter son scan !" )
            
            # Libérer le sémaphore
            shared_memory.user_requests.thread_step_2_tweets_indexer_sem.release()
        
        # Sinon, on vérifie l'état de l'avancement des requêtes qu'on a lancé
        check_list = []
        double_continue = False # Pour faire l'équivalent de deux instruction "continue"
        for scan_request_uri in request.scan_requests :
            scan_request = Pyro4.Proxy( scan_request_uri )
            check_list.append( scan_request.finished_GOT3_indexing and scan_request.finished_TwitterAPI_indexing )
            
            # On vérifie que le scan se passe bien ou s'est bien passé, et si
            # un thread de traitement a planté avec la requête, on l'indique
            if scan_request.has_failed :
                request.problem = "PROCESSING_ERROR"
                
                # On abandonne le processus de traitement de cette requête,
                # même si peut-être qu'on pourrait quand même rechercher
                shared_memory.user_requests.set_request_to_next_step( request, force_end = True )
                double_continue = True
                continue
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_2_tweets_indexer_number" + str(thread_id), None )
        
        # Si l'une des requêtes de scan a eu un problème, on arrête tout avec
        # cette requête utilisateur
        if double_continue :
            continue
        
        # Si toutes nos requêtes ne sont pas finies, on remet la requête en
        # haut de NOTRE file d'attente
        if not all( check_list ) :
            shared_memory.user_requests.step_2_tweets_indexer_queue.put( request )
            continue
        
        # Sinon, on peut vider la liste des requêtes de scan
        request.scan_requests = []
        
        # Et on passe la requête à l'étape suivante
        # C'est la procédure shared_memory.user_requests.set_request_to_next_step
        # qui vérifie si elle peut
        shared_memory.user_requests.set_request_to_next_step( request )
    
    print( "[step_2_th" + str(thread_id) + "] Arrêté !" )
    return
