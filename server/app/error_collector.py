#!/usr/bin/python3
# coding: utf-8

from os import getpid
import traceback
import Pyro4


"""
En vérité, les procédures des threads ne sont pas exécutées directement, mais
le sont par ce collecteur d'erreur.
@param thread_procedure Procédure à exécuter.
@param thread_id ID du thread.
@param shared_memory_uri L'URI menant à la racine du serveur de mémoire
                         partagée Pyro4.
"""
def error_collector( thread_procedure, thread_id : int, shared_memory_uri : str ) :
    # Connexion au serveur de mémoire partagée
    Pyro4.config.SERIALIZER = "pickle"
    shared_memory = Pyro4.Proxy( shared_memory_uri )
    
    # Enregistrer le thread / le procesus
    shared_memory.threads_registry.register_thread( thread_procedure.__name__ + "_number" + str(thread_id), getpid() )
    
    error_count = 0
    while shared_memory.keep_service_alive :
        try :
            thread_procedure( thread_id, shared_memory )
        except Exception as error :
            error_name = "Erreur dans le thread " + str(thread_id) + " de la procédure " + thread_procedure.__name__ + " !\n"
            
            # Mettre la requête en erreur si c'est une requête utilisateur ou
            # une requête de scan
            try :
                request = shared_memory.threads_registry.get_request( thread_procedure.__name__ + "_number" + str(thread_id) )
            # Si on n'est pas un thread de traitement (Utilisateur ou scan)
            except KeyError :
                pass
            # Sinon, si on est un thread de traitement
            else :
                # Si la requête est une requête utilisateur
                # (On est donc un thread de traitement des requêtes utilisateurs)
                if request != None and request.request_type == "user" :
                    request.problem = "PROCESSING_ERROR" # Mettre la requête en erreur
                    shared_memory.user_requests.set_request_to_next_step( request, force_end = True ) # Forcer sa fin
                    error_name += "URL de requête : " + str(request.input_url) + "\n"
                
                # Si la requête est une requête de scan
                # (On est donc un thread de traitement des requêtes de scan)   
                if request != None and request.request_type == "scan" :
                    request.has_failed = True # Mettre la requête en erreur
                    error_name += "Compte Twitter : @" + request.account_name + " (ID " + str(request.account_id) + ")\n"
            
            # Si l'exception s'est produite sur le serveur de mémoire partagée
            if hasattr( error, "_pyroTraceback" ) :
                pyro_traceback = "".join( error._pyroTraceback )
            else :
                pyro_traceback = None
            
            # Enregistrer dans un fichier
            if error_count < 100 : # Ne pas créer trop de fichiers, s'il y a autant d'erreurs, c'est que c'est la même
                file = open( thread_procedure.__name__ + "_number" + str(thread_id) + "_errors.log", "a" )
                file.write( error_name )
                traceback.print_exc( file = file )
                if pyro_traceback != None : file.write( pyro_traceback )
                file.write( "\n\n\n" )
                file.close()
            
            # Afficher dans le terminal
            print( error_name )
            traceback.print_exc()
            if pyro_traceback != None : print( pyro_traceback )
            
            error_count += 1
