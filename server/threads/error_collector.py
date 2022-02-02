#!/usr/bin/python3
# coding: utf-8

from os import getpid
import traceback
import Pyro4
import time
from datetime import datetime

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
from shared_memory.open_proxy import open_proxy
from threads.network_crash import is_network_crash
from threads.network_crash import network_available


# Petit collecteur d'erreurs au collecteur d'erreur général (Ci-dessous).
# Car notre gros collecteur d'erreurs fait beaucoup de choses.
# Doit être le plus minimal possible, car c'est notre dernière chance.
def error_collector( *args, **kwargs ) :
    try :
        _error_collector( *args, **kwargs )
    except Exception :
        error_name = "Erreur dans le collecteur d'erreur général !\n"
        error_name += f"S'est produite le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.\n"
        error_name += "Si vous voyez ceci, c'est que c'est vraiment la merde.\n"
        error_name += "Le thread ne sera pas redémarré, pouvant mener à un dysfonctionnement du serveur\n"
        
        file = open( "error_collector_errors.log", "a" )
        file.write( "ICI LE COLLECTEUR D'ERREURS DE SECOURS !\n" )
        file.write( "Je suis dans le fichier suivant : threads/error_collector.py\n" )
        file.write( error_name )
        traceback.print_exc( file = file )
        file.write( "\n\n\n" )
        file.close()
        
        print( error_name )
        traceback.print_exc()


"""
En vérité, les procédures des threads ne sont pas exécutées directement, mais
le sont par ce collecteur d'erreur.

ATTENTION : La ligne de commande (Dans "app.py") et le thread du serveur de
mémoire partagée Pyro ne doivent pas être exécutés dans ce collecteur
d'erreurs. Seules les procédures de threads présentes dans le module "app"
peuvent l'être.

@param thread_procedure Procédure à exécuter.
@param thread_id ID du thread.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro, ou directement l'objet de mémoire
                         partagée si on n'est pas en mode multi-processus.
"""
def _error_collector( thread_procedure, thread_id : int, shared_memory_uri : str ) :
    # Connexion au serveur de mémoire partagée
    if param.ENABLE_MULTIPROCESSING :
        Pyro4.config.SERIALIZER = "pickle"
    shared_memory = open_proxy( shared_memory_uri )
    
    # Enregistrer le thread / le procesus
    shared_memory.threads_registry.register_thread( f"{thread_procedure.__name__}_th{thread_id}", getpid() )
    
    error_count = 0
    error_on_init_count = 0
    while shared_memory.keep_threads_alive :
        start_time = time.time()
        
        try :
            thread_procedure( thread_id, shared_memory )
        
        except Exception as error :
            # On détecte d'abord si c'est un problème de déconnexion au réseau
            network_crash = is_network_crash( error )
            
            
            error_name = f"Erreur dans le thread {thread_id} de la procédure {thread_procedure.__name__} !\n"
            error_name += f"S'est produite le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.\n"
            if network_crash :
                error_name += "Cette erreur est dûe à une déconnexion du réseau.\n"
            
            # Mettre la requête en erreur si c'est une requête utilisateur ou
            # une requête de scan
            try :
                request = shared_memory.threads_registry.get_request( f"{thread_procedure.__name__}_th{thread_id}" )
            
            # Si le serveur Pyro est HS, c'est très certainement pour ça qu'une
            # erreur est tombée
            except Exception :
                error_name += "De plus, le serveur de mémoire partagée Pyro semble ne pas répondre.\n"
                
                # On ne fait rien de plus, on plantera sur la boucle "while" si
                # Pyro est vraiment HS
            
            else :
                # Si la requête est une requête utilisateur
                # (On est donc un thread de traitement des requêtes utilisateurs)
                if request != None and request.request_type == "user" :
                    request.problem = "PROCESSING_ERROR" # Mettre la requête en erreur
                    shared_memory.user_requests.set_request_to_next_step( request, force_end = True ) # Forcer sa fin
                    error_name += f"URL de requête : {request.input_url}\n"
                
                # Si la requête est une requête de scan
                # (On est donc un thread de traitement des requêtes de scan)
                if request != None and request.request_type == "scan" :
                    request.has_failed = True # Mettre la requête en erreur
                    error_name += f"Compte Twitter : @{request.account_name} (ID {request.account_id})\n"
            
            # Si l'exception s'est produite sur le serveur de mémoire partagée
            if hasattr( error, "_pyroTraceback" ) :
                pyro_traceback = "".join( error._pyroTraceback )
            else :
                pyro_traceback = None
            
            # Si on est un thread de Link Finder, on avertit que ce problème
            # peut être cause par un bug sur un site supporté
            if thread_procedure.__name__ == "thread_step_1_link_finder" :
                error_name += "Attention : Cette erreur peut être causée par un problème temporaire sur un des sites supportés.\n"
                error_name += "Par conséquent, si elle n'est pas reproductible, il ne vaut mieux pas modifier le code d'AOTF.\n"
            
            # Enregistrer dans un fichier
            if error_count < 100 : # Ne pas créer trop de logs, s'il y a autant d'erreurs, c'est que c'est la même
                file = open( f"{thread_procedure.__name__}_th{thread_id}_errors.log", "a" )
                file.write( "ICI LE COLLECTEUR D'ERREURS GENERAL !\n" )
                file.write( "Je suis dans le fichier suivant : threads/error_collector.py\n" )
                file.write( error_name )
                traceback.print_exc( file = file )
                if pyro_traceback != None : file.write( pyro_traceback )
                file.write( "\n\n\n" )
                file.close()
            
            # Afficher dans le terminal
            print( error_name )
            traceback.print_exc()
            if pyro_traceback != None : print( pyro_traceback )
            
            # Si on a crash en moins de 10 secondes, c'est qu'il y a un
            # problème d'initialisation de la procédure
            if time.time() - start_time < 10 :
                error_on_init_count += 1
                
                # On dort 10 mins * le nombre de fois qu'on a crash à l'init
                wait_time = 600 * error_on_init_count
                end_sleep_time = time.time() + wait_time
                
                print( f"Attente de {wait_time} pour redémarrer !" )
                
                # Ne pas utiliser "wait_until()" ici
                # Le collecteur d'erreur est censé être le plus safe possible,
                # on éviter d'appeler d'autres fonctions
                while True :
                    time.sleep( 3 )
                    if time.time() > end_sleep_time :
                        break
                    if not shared_memory.keep_threads_alive :
                        break
            
            # Attendre du réseau si c'est un problème de déconnexion
            if network_crash :
                while shared_memory.keep_threads_alive :
                    if network_available() : break
                    time.sleep( 3 )
            
            error_count += 1
