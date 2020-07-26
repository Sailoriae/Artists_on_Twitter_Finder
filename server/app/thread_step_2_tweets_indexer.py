#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
if param.FORCE_INTELLIGENT_SKIP_INDEXING :
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
    shared_memory.user_requests.requests_in_thread[ "thread_step_2_tweets_indexer_number" + str(thread_id) ] = None
    
    # Accès direct à la base de données
    # N'UTILISER QUE DES METHODES QUI FONT SEULEMENT DES SELECT !
    if param.FORCE_INTELLIGENT_SKIP_INDEXING :
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
        shared_memory.user_requests.requests_in_thread[ "thread_step_2_tweets_indexer_number" + str(thread_id) ] = request
        
        # Si la requête n'a pas eu les scans de ses comptes Twitter lancés,
        # c'est que c'est la première fois qu'on la voit
        if request.scan_requests == None :
            # On passe la requête à l'étape suivante, c'est à dire notre étape
            shared_memory.user_requests.set_request_to_next_step( request )
            
            # Liste des comptes Twitter dont on doit lancer le scan
            accounts_to_scan = []
            
            # On vérifie d'avord si on peut sauter la mise à jour des comptes
            # déjà dans la base de données
            if param.FORCE_INTELLIGENT_SKIP_INDEXING :
                for (account_name, account_id) in request.twitter_accounts_with_id :
                    if not bdd_direct_access.is_account_indexed( account_id ) :
                        accounts_to_scan.append( (account_name, account_id) )
                    else :
                        print( "[step_2_th" + str(thread_id) + "] @" + account_name + " est déjà dans la BDD, on saute son scan !" )
            else :
                accounts_to_scan = request.twitter_accounts_with_id
            
            # On lance l'indexation, en mode prioritaire car on est une requête
            # utilisateur, et on stocke les requêtes qu'on a créé
            request.scan_requests = []
            for (account_name, account_id) in accounts_to_scan :
                print( "[step_2_th" + str(thread_id) + "] Lancement du scan de @" + account_name + "." )
                request.scan_requests.append(
                    shared_memory.scan_requests.launch_request( account_id,
                                                                account_name,
                                                                is_prioritary = True ) )
        
        # Sinon, on vérifie l'état de l'avancement des requêtes qu'on a lancé
        # Note importante : Nos requêtes ne peuvent pas être annulées car on
        # est un thread utilisateur
        # Seules les requêtes non-prioritaires peuvent être annulées
        check_list = []
        for scan_request in request.scan_requests :
            check_list.append( scan_request.finished_date != None )
            
            # On vérifie quand même que le scan s'est bien passé, et si un
            # thread de traitement a planté avec la requête, on l'indique
            if scan_request.has_failed :
                request.problem = "PROCESSING_ERROR"
                
            # On laisse quand même la requête passer à l'étape 3 de recherche
            # inversée d'image, au cas où
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory.user_requests.requests_in_thread[ "thread_step_2_tweets_indexer_number" + str(thread_id) ] = None
        
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
