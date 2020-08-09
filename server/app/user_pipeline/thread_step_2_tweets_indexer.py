#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep, time
from dateutil.tz import tzlocal
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
            
            # Liste des comptes Twitter dont on doit lancer le scan
            accounts_to_scan = []
            
            for (account_name, account_id) in request.twitter_accounts_with_id :
                
                # Si le compte est déjà en cours de scan, on s'y raccroche
                currently_scanning = shared_memory.scan_requests.get_request( account_id )
                if currently_scanning != None :
                    print( "[step_2_th" + str(thread_id) + "] @" + account_name + " est déjà en cours de scan, on le suit !" )
                    
                    # On passe la requête en prioritaire si nécessaire
                    if not currently_scanning.is_prioritary :
                        shared_memory.scan_requests.launch_request( account_id,
                                                                    account_name,
                                                                    is_prioritary = True )
                    
                    # On suit la progression de cette requête
                    request.scan_requests += [ currently_scanning._pyroUri ] # Ne peut pas faire de append avec Pyro
                
                # Sinon, il faut peut-être lancer un scan
                else :
                    # Si le compte n'est pas déjà indexé, il faut le scanner
                    if not bdd_direct_access.is_account_indexed( account_id ) :
                        print( "[step_2_th" + str(thread_id) + "] @" + account_name + " n'est pas dans la BDD, lancement de son scan !" )
                        accounts_to_scan.append( (account_name, account_id) )
                    
                    # Si le compte est déjà indexé
                    else :
                        # On prend ses deux dernières dates de scan
                        last_scan_1 = bdd_direct_access.get_account_GOT3_last_scan_local_date( account_id )
                        last_scan_2 = bdd_direct_access.get_account_TwitterAPI_last_scan_local_date( account_id )
                        
                        # Si l'une des deux est à NULL, il faut scanner (Mais
                        # théoriquement le thread d'auto-update l'a fait avant
                        # nous)
                        if last_scan_1 == None or last_scan_2 == None :
                            accounts_to_scan.append( (account_name, account_id) )
                        
                        # Sinon, on prendre la date minimale
                        else :
                            min_date = min( last_scan_1, last_scan_2 )
                            
                            # On a besoin de mettre le fuseau horaire dans la
                            # date minimale
                            min_date = min_date.replace( tzinfo = local_tz )
                            
                            # Si cette mise à jour moins 3 jours est plus
                            # vielle que la date de l'illustration, il faut MàJ
                            # (On laisse 3 jours de marge à l'artiste pour
                            # publier sur Twitter)
                            if min_date - datetime.timedelta( days = 3 ) < request.datetime :
                                print( "[step_2_th" + str(thread_id) + "] @" + account_name + " est déjà dans la BDD, mais il faut le MàJ car l'illustration de requête est trop récente !" )
                                accounts_to_scan.append( (account_name, account_id) )
                            else :
                                print( "[step_2_th" + str(thread_id) + "] @" + account_name + " est déjà dans la BDD, on saute son scan !" )
            
            # On lance l'indexation, en mode prioritaire car on est une requête
            # utilisateur, et on stocke les requêtes qu'on a créé
            for (account_name, account_id) in accounts_to_scan :
                request.scan_requests += [
                    shared_memory.scan_requests.launch_request( account_id,
                                                                account_name,
                                                                is_prioritary = True )._pyroUri ] # Ne peut pas faire de append avec Pyro
            
            # Libérer le sémaphore
            shared_memory.user_requests.thread_step_2_tweets_indexer_sem.release()
        
        # Sinon, on vérifie l'état de l'avancement des requêtes qu'on a lancé
        # Note importante : Nos requêtes ne peuvent pas être annulées car on
        # est un thread utilisateur
        # Seules les requêtes non-prioritaires peuvent être annulées
        check_list = []
        for scan_request_uri in request.scan_requests :
            scan_request = Pyro4.Proxy( scan_request_uri )
            check_list.append( scan_request.finished_GOT3_indexing and scan_request.finished_TwitterAPI_indexing )
            
            # On vérifie quand même que le scan s'est bien passé, et si un
            # thread de traitement a planté avec la requête, on l'indique
            if scan_request.has_failed :
                request.problem = "PROCESSING_ERROR"
                
            # On laisse quand même la requête passer à l'étape 3 de recherche
            # inversée d'image, au cas où
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread.set_request( "thread_step_2_tweets_indexer_number" + str(thread_id), None )
        
        # Si toutes nos requêtes ne sont pas finies, on remet la requête en
        # haut de NOTRE file d'attente
        if not all( check_list ) :
            shared_memory.user_requests.step_2_tweets_indexer_queue.put( request )
            continue
        
        # On passe la requête à l'étape suivante, fin du traitement
        # C'est la procédure shared_memory.user_requests.set_request_to_next_step
        # qui vérifie si elle peut
        shared_memory.user_requests.set_request_to_next_step( request )
    
    print( "[step_2_th" + str(thread_id) + "] Arrêté !" )
    return
