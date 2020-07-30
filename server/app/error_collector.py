#!/usr/bin/python3
# coding: utf-8

import traceback


"""
En vérité, les procédures des threads ne sont pas exécutées directement, mais
le sont par ce collecteur d'erreur.
@param thread_procedure Procédure à exécuter.
@param thread_id ID du thread.
@param shared_memory Objet Shared_Memory, mémoire partagée.
"""
def error_collector( thread_procedure, thread_id : int, shared_memory ) :
    error_count = 0
    
    while shared_memory.keep_service_alive :
        try :
            thread_procedure( thread_id, shared_memory )
        except Exception :
            error_name = "Erreur dans le thread " + str(thread_id) + " de la procédure " + thread_procedure.__name__ + " !\n"
            
            # Mettre la requête en erreur si c'est une requête utilisateur, et
            # non une requête de scan
            try :
                request = shared_memory.user_requests.requests_in_thread[ thread_procedure.__name__ + "_number" + str(thread_id) ]
            # Si on n'est pas un thread de traitement des requêtes utilisateurs
            # (Etapes 1, 2 et 3), on aura forcément une KeyError
            except KeyError :
                pass
            else :
                if request != None :
                    request.problem = "PROCESSING_ERROR"
                    shared_memory.user_requests.set_request_to_next_step( request, force_end = True )
                    error_name += "URL de requête : " + str(request.input_url) + "\n"
            
            # Mettre la requête en erreur si c'est une requête de scan, et non
            # une requête utilisateur
            try :
                request = shared_memory.scan_requests.requests_in_thread[ thread_procedure.__name__ + "_number" + str(thread_id) ]
            # Si on n'est pas un thread de traitement des requêtes de scan
            # (Etapes paralléles A, B, C et D), on aura forcément une KeyError
            except KeyError :
                pass
            else :
                if request != None :
                    request.has_failed = True
                    error_name += "Compte Twitter : @" + request.account_name + " (ID " + str(request.account_id) + ")\n"
            
            # Enregistrer dans un fichier
            if error_count < 100 : # Ne pas créer trop de fichiers, s'il y a autant d'erreurs, c'est que c'est la même
                file = open( thread_procedure.__name__ + "_number" + str(thread_id) + "_errors.log", "a" )
                file.write( error_name )
                traceback.print_exc( file = file )
                file.write( "\n\n\n" )
                file.close()
            
            # Afficher dans le terminal
            print( error_name )
            traceback.print_exc()
            
            error_count += 1
