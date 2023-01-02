#!/usr/bin/python3
# coding: utf-8

import queue
from time import sleep

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

import parameters as param
from tweet_finder.class_Tweets_Lister_with_SearchAPI import Tweets_Lister_with_SearchAPI
from tweet_finder.class_Tweets_Lister_with_SearchAPI import Unfound_Account_on_Lister_with_SearchAPI
from tweet_finder.class_Tweets_Lister_with_SearchAPI import Blocked_by_User_with_SearchAPI


"""
ETAPE A du traitement de l'indexation ou de la mise à jour de l'indexation d'un
compte Twitter.
Thread de listage des Tweets d'un compte Twitter en utilisant l'API de recherche
de Twitter.
"""
def thread_step_A_SearchAPI_list_account_tweets( thread_id : int, shared_memory ) :
    # Vérifier qu'on a un bon numéro de thread
    if len( param.TWITTER_API_KEYS ) < thread_id :
        raise AssertionError( "Il doit y avoir autant de threads de listage que de clés d'API dans \"TWITTER_API_KEYS\"." )
    
    # Maintenir ouverts certains proxies vers la mémoire partagée
    shared_memory_threads_registry = shared_memory.threads_registry
    shared_memory_scan_requests = shared_memory.scan_requests
    shared_memory_execution_metrics = shared_memory.execution_metrics
    shared_memory_scan_requests_queues_sem = shared_memory_scan_requests.queues_sem
    shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_prior_queue = shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_prior_queue
    shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_queue = shared_memory_scan_requests.step_A_SearchAPI_list_account_tweets_queue
    shared_memory_scan_requests_step_C_index_tweets_queue = shared_memory_scan_requests.step_C_index_tweets_queue
    
    # Fonction à passer à l'objet "Tweets_Lister_with_TimelineAPI"
    # Permet de mettre les Tweets trouvés dans la file d'attente des Tweets à
    # indexer (Il n'y a pas de vérification de doublon car cela prendrait trop
    # de temps, alors que l'indexation vérifie déjà que le Tweet ne soit pas
    # indexé dans la BDD)
    def tweets_queue_put( tweet_dict : dict ) -> None :
        shared_memory_scan_requests_step_C_index_tweets_queue.put( tweet_dict )
    
    # Initialisation du listeur de Tweets
    searchAPI_lister = Tweets_Lister_with_SearchAPI( param.API_KEY,
                                                     param.API_SECRET,
                                                     param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN"],
                                                     param.TWITTER_API_KEYS[ thread_id - 1 ]["OAUTH_TOKEN_SECRET"],
                                                     param.TWITTER_API_KEYS[ thread_id - 1 ]["AUTH_TOKEN"],
                                                     tweets_queue_put,
                                                     DEBUG = param.DEBUG,
                                                     ENABLE_METRICS = param.ENABLE_METRICS,
                                                     add_step_A_time = shared_memory_execution_metrics.add_step_A_time )
    
    # Dire qu'on ne fait rien
    shared_memory_threads_registry.set_request( f"thread_step_A_SearchAPI_list_account_tweets_th{thread_id}", None )
    
    # Tant que on ne nous dit pas de nous arrêter
    while shared_memory.keep_threads_alive :
        
        # Si on ne peut pas acquérir le sémaphore, on retest le keep_threads_alive
        if not shared_memory_scan_requests_queues_sem.acquire( timeout = 3 ) :
            continue
        
        # On tente de sortir une requête de la file d'attente prioritaire
        try :
            request = shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_prior_queue.get( block = False )
        # Si la queue est vide
        except queue.Empty :
            request = None
        if request == None :
            # On tente de sortir une requête de la file d'attente normale
            try :
                request = shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_queue.get( block = False )
            # Si la queue est vide, on attend une seconde et on réessaye
            except queue.Empty :
                request = None
            if request == None :
                shared_memory_scan_requests_queues_sem.release()
                sleep( 1 )
                continue
        
        # Vérifier qu'on n'est pas bloqué par ce compte
        if thread_id - 1 in request.blocks_list :
            # Si tous les comptes qu'on a pour lister sont bloqués, on met la
            # requête en échec
            if len( request.blocks_list ) >= len( param.TWITTER_API_KEYS ) :
                print( f"[step_A_th{thread_id}] Le compte Twitter @{request.account_name} bloque tous les comptes de listage ! Ses Tweets ne peuvent pas être indexés." )
                request.has_failed = True
            
            # Sinon, on la remet dans la file
            else :
                if request.is_prioritary :
                    shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_prior_queue.put( request )
                else :
                    shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_queue.put( request )
            
            # Lacher le sémaphore et arrêter là, on ne peut pas la traiter
            shared_memory_scan_requests_queues_sem.release()
            request._pyroRelease()
            continue
        
        # Dire qu'on a commencé à traiter cette requête
        # AVANT de lacher le sémaphore !
        request.started_SearchAPI_listing = True
        
        # Lacher le sémaphore
        shared_memory_scan_requests_queues_sem.release()
        
        # Si demandé, reset le curseur d'indexation de ce compte
        # On va donc relister tous ses Tweets (Avec l'API de recherche)
        if request.reset_SearchAPI_cursor :
            searchAPI_lister._bdd.reset_account_SearchAPI_last_tweet_date( request.account_id )
        
        # Vérifier si ce compte n'est pas dans notre liste noire
        # AVANT de se déclarer au registre des threads
        if shared_memory_scan_requests.is_blacklisted( int( request.account_id ) ) :
            print( f"[step_A_th{thread_id}] Le compte Twitter @{request.account_name} est sur notre liste noire ! Ses Tweets ne seront pas listés." )
            request._pyroRelease()
            continue
        
        # Dire qu'on est en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_A_SearchAPI_list_account_tweets_th{thread_id}", request )
        
        # On liste les tweets du compte Twitter de la requête avec l'API de recherche
        print( f"[step_A_th{thread_id}] Listage des Tweets du compte Twitter @{request.account_name} avec l'API de recherche." )
        try :
            searchAPI_lister.list_searchAPI_tweets( request.account_name,
                                                    account_id = request.account_id,
                                                    request_uri = request._pyroUri )
        except Unfound_Account_on_Lister_with_SearchAPI :
            print( f"[step_A_th{thread_id}] Le compte Twitter @{request.account_name} (ID {request.account_id}) n'existe pas." )
            request.unfound_account = True
        
        except Blocked_by_User_with_SearchAPI :
            print( f"[step_A_th{thread_id}] Le compte Twitter @{request.account_name} bloque le compte de listage de ce thread. Un autre thread de listage le réessayera." )
            request.blocks_list += [ thread_id - 1 ] # Ne peut pas faire de append avec Pyro
            if request.is_prioritary :
                shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_prior_queue.put( request )
            else :
                shared_memory_scan_requests_step_A_SearchAPI_list_account_tweets_queue.put( request )
        
        # En cas de plantage lors du listage, il faut envoyer une instruction
        # d'enregistrement du curseur afin que la requête de scan soit terminée
        # proprement lorsque tous les Tweets qui ont pu être listés seront
        # enregistrés
        except Exception as error:
            request.has_failed = True # A faire avant
            searchAPI_lister._send_save_cursor_instruction( request.account_name,
                                                            request.account_id,
                                                            request._pyroUri,
                                                            unchange_cursor = True )
            raise error # Passer au collecteur d'erreurs
        
        # Dire qu'on n'est plus en train de traiter cette requête
        shared_memory_threads_registry.set_request( f"thread_step_A_SearchAPI_list_account_tweets_th{thread_id}", None )
        
        # Forcer la fermeture du proxy
        request._pyroRelease()
    
    print( f"[step_A_th{thread_id}] Arrêté !" )
    return
