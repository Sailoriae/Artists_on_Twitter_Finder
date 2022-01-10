#!/usr/bin/python3
# coding: utf-8

import Pyro4
import threading
import datetime
from time import time, sleep
import queue
import copy

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
    change_wdir( ".." )
    path.append(get_wdir())

from shared_memory.class_Scan_Request import Scan_Request
from shared_memory.remove_account_id_from_queue import remove_account_id_from_queue
from shared_memory.class_Pyro_Semaphore import Pyro_Semaphore
from shared_memory.class_Pyro_Queue import Pyro_Queue
from shared_memory.open_proxy import open_proxy
from tweet_finder.blacklist import BLACKLIST


"""
Classe de gestion des requêtes d'indexation (Nouvelle ou mise à jour) comptes
Twitter dans la base de données.
Instanciée une seule fois lors de l'unique instanciation de la mémoire
partagée, c'est à dire de la classe Shared_Memory.

Les requêtes sont identifiées par l'ID du compte Twitter.

Attention : Ce pipeline de traitement est parallélisé, et non étapes par
étapes !

Note : Pour les objets, on stocke en réalité l'URI qui mène à l'objet sur le
serveur Pyro, et pas l'objet directement (Car Pyro ne peut pas exécuter sur le
serveur les méthodes des sous-objets), et pas le Proxy vers l'objet (Car un
Proxy ne peut être utilisé que par un seul thread à la fois).
Les files d'attente contiennent donc des URI, c'est à dire des chaines de
caractères.
"""
@Pyro4.expose
class Scan_Requests_Pipeline :
    def __init__ ( self, root_shared_memory ) :
        self._root = root_shared_memory
        
        # Comme les objets dans la mémoire partagée sont identifiées par leur
        # URI, et donc uniques, on peut faire le dictionnaire de correspondance
        # suivant :
        # Clé : URL de requête -> Valeur : URI de l'objet Scan_Request.
        self._requests = {}
        
        # Sémaphore d'accès au dictionnaire précédent.
        self._requests_sem = threading.Semaphore()
        
        # File d'attente à l'étape A du traitement : Listage des Tweets avec
        # l'API de recherche.
        # Les objets queue.Queue sont prévus pour faire du multi-threading.
        self._step_A_SearchAPI_list_account_tweets_prior_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_A_SearchAPI_list_account_tweets_prior_queue = self._root.register_obj( self._step_A_SearchAPI_list_account_tweets_prior_queue_obj )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_A_SearchAPI_list_account_tweets_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_A_SearchAPI_list_account_tweets_queue = self._root.register_obj( self._step_A_SearchAPI_list_account_tweets_queue_obj )
        
        # File d'attente à l'étape B du traitement : Listage des Tweets avec
        # l'API de timeline.
        self._step_B_TimelineAPI_list_account_tweets_prior_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_B_TimelineAPI_list_account_tweets_prior_queue = self._root.register_obj( self._step_B_TimelineAPI_list_account_tweets_prior_queue_obj )
        
        # Version non-prioritaire de la file d'attente précédente.
        self._step_B_TimelineAPI_list_account_tweets_queue_obj = Pyro_Queue( convert_uri = True )
        self._step_B_TimelineAPI_list_account_tweets_queue = self._root.register_obj( self._step_B_TimelineAPI_list_account_tweets_queue_obj )
        
        # Bloquer toutes les 4 files d'attentes ci-dessus. Permet de passer une
        # requête en prioritaire sans avoir de problème.
        self._queues_sem_obj = Pyro_Semaphore()
        self._queues_sem = self._root.register_obj( self._queues_sem_obj )
        
        # File d'attente à l'étape C du traitement : Indexation des Tweets.
        # Cette file est universelle, c'est à dire qu'elle est utilisé peu
        # importe dans quel listage le Tweet a été trouvé.
        # Il n'y a pas de version prioritaire, de cette file, car on perdrait
        # trop de temps à sortir les Tweets. De plus, cela casserait l'ordre
        # des instructions d'enregistrement de curseurs. Car cette liste peut
        # aussi contenir des instruction d'enregistrement de curseurs
        # d'indexation, qui sont exécutées par les threads de l'étapt C.
        self._step_C_index_account_tweet_queue_obj = Pyro_Queue( convert_uri = False )
        self._step_C_index_account_tweets_queue = self._root.register_obj( self._step_C_index_account_tweet_queue_obj )
        
        # Dictionnaire des Tweets en cours d'indexation.
        # Les threads de l'étape C déclarent dedans l'ID du Tweet qu'ils sont
        # en train de traiter, ainsi que l'ID du compte Twitter associé. Cela
        # permet de vérifier qu'ils  aient tous fini avant d'enregistrer les
        # curseurs.
        self._indexing_ids_dict = {}
        
        # Sémaphore de protection de sortie de la file d'attente de l'étape C
        # et du dictionnaire des Tweets en cours d'indexation. Permet d'être
        # certain qu'un Tweet sorti soit déclaré. Resté interne.
        self._step_C_sem = Pyro_Semaphore()
        
        # Compteur du nombre de requêtes en cours de traitement dans le
        # pipeline.
        self._processing_requests_count = 0
        
        # Liste des IDs de comptes Twitter qui sont dans la liste noire des
        # comptes à ne pas indexer.
        self._blacklist = BLACKLIST
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def step_A_SearchAPI_list_account_tweets_prior_queue( self ) : return open_proxy( self._step_A_SearchAPI_list_account_tweets_prior_queue )
    
    @property
    def step_A_SearchAPI_list_account_tweets_queue( self ) : return open_proxy( self._step_A_SearchAPI_list_account_tweets_queue )
    
    @property
    def step_B_TimelineAPI_list_account_tweets_prior_queue( self ) : return open_proxy( self._step_B_TimelineAPI_list_account_tweets_prior_queue )
    
    @property
    def step_B_TimelineAPI_list_account_tweets_queue( self ) : return open_proxy( self._step_B_TimelineAPI_list_account_tweets_queue )
    
    @property
    def queues_sem( self ) : return open_proxy( self._queues_sem )
    
    @property
    def step_C_index_account_tweets_queue( self ) : return open_proxy( self._step_C_index_account_tweets_queue )
    
    @property
    def processing_requests_count( self ) : return self._processing_requests_count
    
    # Obtenir le nombre de requêtes en mémoire
    def get_size( self ) :
        # Pas besoin de prendre le sémaphore, le GIL Pyhton fait son job
        return len( self._requests )
    
    # Savoir si un ID de compte est dans la liste noire ou pas
    # Permet de ne pas transférer la liste (Lourde en mémoire)
    def is_blacklisted( self, account_id : int ) -> bool :
        return int( account_id ) in self._blacklist
    
    """
    Lancer l'indexation ou la mise à jour de l'indexation d'un compte Twitter
    dans la base de données.
    Crée une nouvelle requête si ce compte n'est pas déjà en cours de scan.
    Si le compte était déjà en cours de scan (Ou en file d'attente), il est mis
    en prioritaire si il ne l'était pas déjà et que c'est demandé ici.
    A l'inverse, une requête prioritaire n'est pas tranformée en requête
    non-prioritaire.
    
    Une requête déjà existante peut être terminée ! Ainsi, cela permet de ne
    pas réindexer directement le compte Twitter.
    Les requêtes sont délestées par le thread "remove_finished_requests" 24h
    après la fin de son traitement, permettant de rescanner le compte Twitter.
    
    @param account_id L'ID du compte Twitter. Ne sert qu'à identifier.
    @param account_name Le nom du compte Twitter. Attention, c'est lui qui est
                        revérifié et scanné !
    @param is_prioritary Est ce que cette requête est prioritaire ?
    
    @return L'objet Scan_Request créé.
            Ou l'objet Scan_Request déjà existant.
    """
    def launch_request ( self, account_id : int,
                               account_name : str,
                               is_prioritary : bool = False ) -> Scan_Request :
        account_id = int(account_id) # Sécurité, pour unifier
        
        requests_sem = self._requests_sem
        queues_sem = self._queues_sem_obj
        
        requests_sem.acquire()
        queues_sem.acquire()
        
        # Vérifier d'abord qu'on n'est pas déjà en train de traiter ce compte.
        for key in self._requests :
            if key == account_id :
                request = open_proxy( self._requests[key] )
                
                # Si il faut passer la requête en proritaire.
                if is_prioritary and not request.is_prioritary :
                    request.is_prioritary = True
                
                # Si on peut passer la requête en proritaire.
                if ( is_prioritary and
                     not request.is_prioritary and
                     not request.has_failed and
                     not request.unfound_account ) :
                    request.is_prioritary = True
                    
                    # Si est dans une file d'attente de listage des Tweets avec
                    # l'API de recherche, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if not request.started_SearchAPI_listing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        remove_account_id_from_queue(
                            self._step_A_SearchAPI_list_account_tweets_queue_obj,
                            account_id )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        self._step_A_SearchAPI_list_account_tweets_prior_queue_obj.put( request )
                    
                    # Si est dans une file d'attente de listage des Tweets avec
                    # l'API de timeline, on la sort, pour la mettre dans la même
                    # file d'attente, mais prioritaire.
                    if not request.started_TimelineAPI_listing :
                        # On doit démonter et remonter la file en enlevant la
                        # requête.
                        remove_account_id_from_queue(
                            self._step_B_TimelineAPI_list_account_tweets_queue_obj,
                            account_id )
                        
                        # On met la requête dans la file d'attente prioritaire.
                        self._step_B_TimelineAPI_list_account_tweets_prior_queue_obj.put( request )
                
                queues_sem.release()
                requests_sem.release()
                return request
        
        # Créer et ajouter l'objet Scan_Request à notre système.
        request = self._root.register_obj( Scan_Request( account_id,
                                                         account_name,
                                                         is_prioritary = is_prioritary ) )
        self._processing_requests_count += 1 # Augmenter le compteur du nombre de requêtes en cours de traitement
        self._requests[ account_id ] = request # On passe ici l'URI de l'objet.
        
        request = open_proxy( request )
        
        # Comme le traitement des requêtes de scan est parallélisé, on peut
        # mettre la requêtes dans les deux files d'attente de listage.
        if is_prioritary :
            self._step_A_SearchAPI_list_account_tweets_prior_queue_obj.put( request )
            self._step_B_TimelineAPI_list_account_tweets_prior_queue_obj.put( request )
        else :
            self._step_A_SearchAPI_list_account_tweets_queue_obj.put( request )
            self._step_B_TimelineAPI_list_account_tweets_queue_obj.put( request )
        
        queues_sem.release()
        requests_sem.release()
        
        # Retourner l'objet Scan_Request.
        return request
    
    """
    Obtenir l'objet Scan_Request d'une requête.
    
    @param account_id L'ID du compte Twitter.
    @return Un objet Scan_Request,
            Ou None si la requête est inconnue.
    """
    def get_request ( self, account_id : int ) -> Scan_Request :
        account_id = int(account_id) # Sécurité, pour unifier
        
        self._requests_sem.acquire()
        for key in self._requests :
            if key == account_id :
                self._requests_sem.release()
                return open_proxy( self._requests[key] )
        self._requests_sem.release()
        
        return None
    
    """
    Marquer une requête comme terminée.
    Fonction à appeler par un thread d'indexation (Etape C) lors de chaque
    instruction d'enregistrement de curseur.
    
    @param Un objet Scan_Request.
    @param get_stats Le résultat de la méthode "get_stats()" de l'objet
                     "SQLite_or_MySQL". Car Pyro est multithreadé, donc on ne
                     peut pas avoir notre propre accès à la BDD !
    
    @retrun True si les threads d'indexation ont tous avancé et donc qu'on peut
            enregistrer le curseur. False sinon, ou si un thread a planté (La
            requête de scan a été mise en échec).
    
    Cette fonction attend que les threads d'indexation n'indexent plus un
    Tweet du compte Twitter placé dans la file avant l'appel à cette fonction.
    Cela permet d'enregistrer les curseurs une fois qu'on est certain que tous
    les Tweets trouvé avec un listeur sont enregistrés dans la BDD.
    Il faut donc appeler cette fonction à chaque fois qu'un thread d'indexation
    rencontre une instruction d'enregistrement de curseur.
    """
    def end_request ( self, request : Scan_Request, get_stats = None ) :
        # Vérifier que les threads d'indexations avancent et ne sont pas
        # bloqués avec un Tweet placé dans la file de l'étape C avant
        # l'instruction d'enregistrement du curseur
        # Cela permet d'être certain que tous les Tweets listés par un des
        # listeurs sont enregistrés dans la base de données (Car les Tweets
        # listés sont placés dans la file avant le curseur)
        # On commence par prendre une snapshot du dictionnaire des Tweets
        # en cours d'indexation, puis on attend que chaque thread avance pour
        # le compte Twitter de la requête de scan
        self._step_C_sem.acquire()
        indexing_ids_dict_snapshot = copy.deepcopy( self._indexing_ids_dict )
        self._step_C_sem.release()
        for thread_name in self._indexing_ids_dict :
            count = 0 # Pour ne pas afficher le message les premières fois
            # On ne vérifie pas "keep_threads_alive" car un thread d'indexation
            # n'est pas censé prendre trop de temps sur l'indexation d'un Tweet
            # Sinon, c'est qu'il y a un bug, et ceci permet de le détecter
            while True :
                count += 1
                tweet_id, account_id = self._indexing_ids_dict[thread_name]
                if ( tweet_id != None and
                     account_id == request.account_id and
                     tweet_id == indexing_ids_dict_snapshot[thread_name][0] ) :
                    if count > 10 :
                        print( f"[end_request] Attente du thread {thread_name}, il est en train d'indexer le Tweet ID {tweet_id} de @{request.account_name}." )
                    sleep( 1 )
                else :
                    break
        
        # On peut Màj les statistiques mises en cache dans l'objet racine
        # Pas besoin de sémaphore, le GIL de Python nous garantie qu'il n'y
        # aura pas deux écritures en même temps
        if get_stats != None :
            self._root.tweets_count, self._root.accounts_count = get_stats
        
        # On passe maintenant à l'éventuelle fin de la requête de scan, et donc
        # on vérifie avant que les deux indexations soient terminées
        if not request.finished_SearchAPI_indexing or not request.finished_TimelineAPI_indexing :
            # Vérifier que la requête de scan n'ait pas été mise en échec
            if request.has_failed : return False
            return True
        
        self._requests_sem.acquire()
        
        # Si la requête n'a pas déjà été marquée comme terminée
        if request.finished_date == None :
            # On indique la date de fin du scan
            request.finished_date = datetime.datetime.now()
            
            # On fais -1 au compteur du nombre de requêtes en cours de traitement
            self._processing_requests_count -= 1
            
            # On peut lacher le sémaphore
            self._requests_sem.release()
            
            # Enregistrer le temps complet pour traiter cette requête
            self._root._execution_metrics_obj.add_scan_request_full_time( time() - request.start )
        
        else :
            self._requests_sem.release()
        
        # Vérifier que la requête de scan n'ait pas été mise en échec
        if request.has_failed : return False
        return True
    
    """
    Délester les anciennes requêtes.
    """
    def shed_requests ( self ) :
        # On prend la date actuelle
        now = datetime.datetime.now()
        
        # On bloque l'accès la liste des requêtes
        self._requests_sem.acquire()
        
        # On filtre la liste des requêtes de scan
        new_requests_dict = {}
        to_unregister_list = []
        
        for key in self._requests :
            request_uri = self._requests[key]
            request = self._root.get_obj( request_uri )
            
            # Si la requête est terminée, il faut vérifier qu'on puisse la garder
            if request.finished_date != None :
                
                # Si la date de fin est à moins de 24h de maintenant, on garde
                # cette requête
                if now - request.finished_date < datetime.timedelta( hours = 24 ) :
                    new_requests_dict[ key ] = request_uri
                
                else : # On désenregistre la requête
                    to_unregister_list.append( request_uri )
            
            # Sinon, son traitement n'est pas fini, on la garde forcément
            else :
                new_requests_dict[ key ] = request_uri
        
        # On installe la nouvelle liste
        self._requests = new_requests_dict
        
        # On débloque l'accès à la liste des requêtes
        self._requests_sem.release()
        
        # On désenregistre les requêtes à désenregistrer
        for uri in to_unregister_list :
            self._root.unregister_obj( uri )
    
    """
    Pour les threads d'indexation (Etape C), obtenir un Tweet dans la file des
    Tweets à indexer, et déclarer cet ID de Tweet, ainsi que l'ID du compte
    Twitter associé, le tout dans un sémaphore.
    Permet de sécuriser la fin d'une requête de scan, et l'enregistrement
    des curseurs.
    Si il n'y a pas de Tweet à sortir, ou que le dictionnaire n'est pas un
    Tweet, le thread est automatiquement déclaré comme en attente.
    
    @param thread_name L'identifiant du thread.
    @param first_time Permet de dire que c'est notre première déclaration, et
                      donc vérifie qu'on n'écrase pas un Tweet ans le
                      dictionnaire des Tweets en cours d'indexation.
    @return Un dictionnaire de Tweet à indexer, au format de sortie de la
            fonction "analyse_tweet_json()".
            Ou None si la file est vide.
    """
    def get_tweet_to_index ( self, thread_name, first_time = False ) -> dict :
        self._step_C_sem.acquire()
        if first_time and thread_name in self._indexing_ids_dict :
            if self._indexing_ids_dict[ thread_name ] != (None, None) :
                self._step_C_sem.release()
                raise AssertionError( f"Le thread \"{thread_name}\" déclare sa première indexation, mais il y a déjà un Tweet dans le dictionnaire des Tweets en cours d'indexation associé à ce nom de thread." )
        try :
            tweet = self._step_C_index_account_tweet_queue_obj.get( block = False )
        except queue.Empty :
            tweet = None
        if tweet == None :
            self._indexing_ids_dict[ thread_name ] = (None, None)
            self._step_C_sem.release()
            return None
        if "tweet_id" in tweet :
            self._indexing_ids_dict[ thread_name ] = ( int(tweet["tweet_id"]), int(tweet["user_id"]) )
        else :
            self._indexing_ids_dict[ thread_name ] = (None, None)
        self._step_C_sem.release()
        return tweet
        
    """
    Obtenir ce qu'un thread d'indexation (Etape C) est en train de faire.
    
    @param thread_name L'identifiant du thread.
    @return Un tuple, contenant l'ID du Tweet, et l'ID du compte Twitter
            associé, ou (None, None) se le thread est en attente.
    """
    def get_indexing_ids ( self, thread_name : str ) :
        if not thread_name in self._indexing_ids_dict :
            raise AssertionError( f"Le thread \"{thread_name}\" ne s'est pas enregistré comme thread d'indexation (Etape C) !" )
        return self._indexing_ids_dict[ thread_name ]
