#!/usr/bin/python3
# coding: utf-8

import os
import sys
import signal
from time import sleep
from datetime import datetime
import traceback

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

import parameters as param
from app.define_max_file_descriptors import define_max_file_descriptors
from app.class_Debug_File import Debug_File

from shared_memory.launch_shared_memory import launch_shared_memory

from threads.threads_launchers import launch_thread
from threads.threads_launchers import launch_identical_threads_in_container
from threads.threads_launchers import launch_unique_threads_in_container
from threads.threads_launchers import write_stacks

from threads.user_pipeline.thread_step_1_link_finder import thread_step_1_link_finder
from threads.user_pipeline.thread_step_2_tweets_indexer import thread_step_2_tweets_indexer
from threads.user_pipeline.thread_step_3_reverse_search import thread_step_3_reverse_search

from threads.scan_pipeline.thread_step_A_SearchAPI_list_account_tweets import thread_step_A_SearchAPI_list_account_tweets
from threads.scan_pipeline.thread_step_B_TimelineAPI_list_account_tweets import thread_step_B_TimelineAPI_list_account_tweets
from threads.scan_pipeline.thread_step_C_index_tweets import thread_step_C_index_tweets
from threads.scan_pipeline.thread_retry_failed_tweets import thread_retry_failed_tweets

from threads.http_server.thread_http_server import thread_http_server

from threads.maintenance.thread_auto_update_accounts import thread_auto_update_accounts
from threads.maintenance.thread_reset_SearchAPI_cursors import thread_reset_SearchAPI_cursors
from threads.maintenance.thread_remove_finished_requests import thread_remove_finished_requests


"""
Cette classe est le gestionnaire des threads du serveur AOTF. Elle permet de
les démarrer et de les éteindre, ainsi que de gérer les signaux demandant
l'arrêt du serveur. Cette classe doit être instanciée qu'une seule fois.
"""
class Threads_Manager :
    """
    Constructeur : Initialise les attributs privés.
    """
    def __init__ ( self ) :
        # PID de "app.py". Permet d'éviter que les processus fils éxécutent la
        # même fonction d'écoute des signaux (Si "fork" sous Unix).
        self._pid = os.getpid()
        
        # Ecouter les signaux nous demandant d'arrêter le serveur
        signal.signal( signal.SIGINT, self.on_sigterm )
        signal.signal( signal.SIGTERM, self.on_sigterm )
        try : signal.signal(signal.SIGHUP, self.on_sigterm)
        except AttributeError : pass # Windows
        
        # Fichier de débug
        self._debug = Debug_File()
        
        # Proxies vers la mémoire partagée si on est en mode multi-processus,
        # sinon objet racine de la mémoire partagée
        self._shared_memory = None
        
        # Objet de thread du serveur Pyro si on est en multi-processus
        self._thread_pyro = None
        
        # Liste des threads XOR processus si on est en multi-processus
        self._threads_xor_process = []
        
        # Permet de ne pas démarrer deux fois le serveur
        self._launch_started = False
        
        # Permet de ne pas oublie des processus fils si on éteint le serveur
        # alors qu'on est en train de les créer
        self._launch_in_progress = False
        
        # Permet de ne lancer qu'une seule fois la procédure d'extinction
        self._stop_started = False
    
    """
    Fonction appelée lorsqu'on reçoit un signal nous demandant d'arrêter le
    serveur AOTF.
    """
    def on_sigterm ( self, signum, frame ) :
        # Eviter que les processus fils éxécutent cette fonction
        if self._pid != os.getpid() : return
        
        self._debug.write( f"[Threads_Manager] Signal {signal.Signals(signum).name} reçu." )
        
        # Si on a reçu un signal "SIGHUP", c'est très certainement que la
        # screen dans laquelle on est contenu n'existe plus, et donc que STDOUT
        # est fermé. Il faut informer nos processus fils si on est en mode
        # multi-processus, et restaurer notre STDOUT.
        is_sighup = False
        try : is_sighup = signum == signal.SIGHUP.numerator
        except AttributeError : pass # Windows
        if is_sighup :
            if param.ENABLE_MULTIPROCESSING :
                for process in self._threads_xor_process :
                    os.kill( process.pid, signal.SIGHUP )
            sys.stdout = open( os.devnull, "w" )
        
        self.stop_threads()
    
    """
    Fonction permettant de lancer les threads du serveur AOTF.
    
    Ce ne sont pas les procédures qui sont exécutées directement, mais le
    collecteur d'erreurs qui exécute la procédure. Voir les fonctions du
    fichier "threads_launchers.py". Ce sont elles qui lancent réellement les
    threads et les processus fils.
    
    La seule exception est le thread du serveur Pyro, qui a sa propre fonction
    de démarrage, et son propre collecteur d'erreurs. Si on n'est pas en mode
    multi-processus, la mémoire partagée est un simple objet.
    
    IMPORTANT : Si on est en multi-processus, aucun thread ne doit être créé
    directement en tant que fils de "app.py", car il y a déjà le serveur Pyro.
    Les procédures qui peuvent rester des threads afin d'économiser de la RAM
    doivent être exécutés dans un processus conteneur.
    """
    def launch_threads ( self ) :
        if self._launch_started : return
        if self._stop_started : return
        self._launch_started = True
        self._launch_in_progress = True
        
        print( f"[Threads_Manager] Démarrage des {'processus et threads' if param.ENABLE_MULTIPROCESSING else 'threads'}." )
        self._debug.write( f"[Threads_Manager] Démarrage des {'processus et threads' if param.ENABLE_MULTIPROCESSING else 'threads'}." )
        
        # Augmenter le nombre maximal de descripteurs de fichiers et
        # démarrer le serveur de mémoire partagée
        max_fd = define_max_file_descriptors()
        self._shared_memory, self._thread_pyro = launch_shared_memory( max_fd )
        
        # Si échec du lancement du serveur de mémoire partagée
        if self._shared_memory == None :
            self._launch_in_progress = False
            self.stop_threads()
            return
        
        # Si l'arrêt a démarré pendant qu'on lançait la mémoire, on ne va pas
        # plus loin dans le démarrage du serveur
        if self._stop_started :
            self._launch_in_progress = False
            return
        
        # Threads étape 1 (Link Finder)
        self._threads_xor_process.extend(
            launch_identical_threads_in_container(
                thread_step_1_link_finder,
                param.NUMBER_OF_STEP_1_LINK_FINDER_THREADS,
                False, # Ne nécessitent pas des processus séparés
                self._shared_memory.get_URI() ) )
        
        # Threads étape 2 : Lancement de l'indexation ou mise à jour
        self._threads_xor_process.extend(
            launch_identical_threads_in_container(
                thread_step_2_tweets_indexer,
                param.NUMBER_OF_STEP_2_TWEETS_INDEXER_THREADS,
                False, # Ne nécessitent pas des processus séparés
                self._shared_memory.get_URI() ) )
        
        # Threads étape 3 : Recherche par image
        self._threads_xor_process.extend(
            launch_identical_threads_in_container(
                thread_step_3_reverse_search,
                param.NUMBER_OF_STEP_3_REVERSE_SEARCH_THREADS,
                True, # Nécessitent des processus séparés (Recherche par image)
                self._shared_memory.get_URI() ) )
        
        # Threads étape A : Listage avec l'API de recherche
        self._threads_xor_process.extend(
            launch_identical_threads_in_container(
                thread_step_A_SearchAPI_list_account_tweets,
                len( param.TWITTER_API_KEYS ), # Threads de listage
                False, # Ne nécessitent pas des processus séparés
                self._shared_memory.get_URI() ) )
        
        # Threads étape B : Listage avec l'API de timeline
        self._threads_xor_process.extend(
            launch_identical_threads_in_container(
                thread_step_B_TimelineAPI_list_account_tweets,
                len( param.TWITTER_API_KEYS ), # Threads de listage
                False, # Ne nécessitent pas des processus séparés
                self._shared_memory.get_URI() ) )
        
        # Threads étape C : Indexation des Tweets trouvés
        self._threads_xor_process.extend(
            launch_identical_threads_in_container(
                thread_step_C_index_tweets,
                param.NUMBER_OF_STEP_C_INDEX_TWEETS,
                True, # Nécessitent des processus séparés (Analyse d'images)
                self._shared_memory.get_URI() ) )
        
        
        # On ne crée qu'un seul thread (ou processus) du serveur HTTP
        # C'est lui qui va créer plusieurs threads grace à la classe :
        # http.server.ThreadingHTTPServer()
        self._threads_xor_process.append(
            launch_thread(
                thread_http_server,
                1, True, # Nécessite un processus séparé (Serveur HTTP)
                self._shared_memory.get_URI() ) )
        
        
        # Liste des procédures de maintenance (Doivent être uniques)
        maintenance_procedures = []
        maintenance_procedures.append( thread_auto_update_accounts )
        maintenance_procedures.append( thread_reset_SearchAPI_cursors )
        maintenance_procedures.append( thread_remove_finished_requests )
        maintenance_procedures.append( thread_retry_failed_tweets )
        
        # Lancer les procédures de maintenance
        self._threads_xor_process.extend(
            launch_unique_threads_in_container(
                maintenance_procedures,
                False, # Ne nécessitent pas des processus séparés
                "thread_maintenance", # Convention de nommage
                self._shared_memory.get_URI() ) )
        
        self._launch_in_progress = False
    
    """
    Ecrire les piles d'appels des threads du serveur AOTF.
    """
    def write_stacks ( self ) :
        file = open( "stacktrace.log", "a", encoding = "utf-8" )
        file.write( f"ETAT DU SERVEUR AOTF LE {datetime.now().strftime('%Y-%m-%d A %H:%M:%S')} :\n" )
        file.write( self._shared_memory.threads_registry.get_status() + "\n" )
        file.write( "\n\n\n" )
        file.close()
        
        if param.ENABLE_MULTIPROCESSING :
            if self._shared_memory != None :
                self._shared_memory.processes_registry.write_stacks()
        
        else :
            write_stacks( self._threads_xor_process )
    
    """
    Fonction permettant d'arrêter les threads du serveur AOTF. Utilisée lors de
    la fin de la fin de la CLI (Commande "stop"), ou lors des signaux gérés par
    cette classe.
    
    Cette fonction attend que les threads se terminent, puis arrête la mémoire
    partagée (Pyro) si on est en multi-processus.
    """
    def stop_threads ( self ) :
        # Vérifier que la procédure d'arrêt n'a pas déjà été appelée.
        if self._stop_started : return
        self._stop_started = True
        
        self._debug.write( "[Threads_Manager] Arrêt initié." )
        
        # Si on est avant le démarrage des threads, la mémoire partagée ni
        # aucun thread n'existe. On peut donc s'arrêter sans rien faire.
        if not self._launch_started :
            try : print( "Démarrage annulé." )
            except OSError : pass # Par mesure de sécurité
        
        # Sinon, il faut quand même prendre des précautions, car il se peut que
        # le serveur ne soit pas totalement démarré.
        else :
            try : print( "[Threads_Manager] Arrêt à la fin des procédures en cours..." )
            except OSError : pass # Par mesure de sécurité
            
            if self._shared_memory != None :
                self._shared_memory.keep_threads_alive = False
            
            # Attendre si le lancement était en cours (Maximum 60 secondes)
            for i in range(6) :
                if not self._launch_in_progress : break
                try : print( "[Threads_Manager] Lancement déjà en cours, attente de 10 secondes..." )
                except OSError : pass # Par mesure de sécurité
                sleep( 10 )
            
            # Attendre que les threads aient terminé
            for thread in self._threads_xor_process :
                thread.join()
            
            # Eteindre le serveur de mémoire partagée
            if param.ENABLE_MULTIPROCESSING :
                if self._shared_memory != None :
                    self._shared_memory.keep_pyro_alive = False
                    self._thread_pyro.join()
        
        self._debug.write( "[Threads_Manager] Arrêt terminé." )
        self._debug.close()
        
        sys.stdin.close() # Pour terminer la CLI (A la fin car ça peut crasher)
        sys.exit(0)
        
        # Eviter d'utiliser "os._exit(0)", ça fait de la merde dans le terminal
        # lorsqu'on en reprend le contrôle. En plus ça ne nettoie rien.
