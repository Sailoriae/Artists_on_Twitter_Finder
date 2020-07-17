#!/usr/bin/python3
# coding: utf-8

import traceback


"""
En vérité, les procédures des threads ne sont pas exécutées directement, mais
le sont par ce collecteur d'erreur.
@param thread_procedure Procédure à exécuter.
@param thread_id ID du thread.
@param pipeline Objet Pipeline, mémoire partagée.
"""
def error_collector( thread_procedure, thread_id : int, pipeline ) :
    error_count = 0
    
    while pipeline.keep_service_alive :
        try :
            thread_procedure( thread_id, pipeline )
        except Exception :
            error_name = "Erreur dans le thread " + str(thread_id) + " de la procédure " + thread_procedure.__name__ + " !\n"
            
            # Mettre la requête en erreur
            try :
                request = pipeline.requests_in_thread[ thread_procedure.__name__ + "_number" + str(thread_id) ]
            except KeyError : # Si on est un thread du serveur HTTP, on aura forcément une KeyError
                pass
            else :
                if request != None :
                    request.problem = "PROCESSING_ERROR"
                    request.set_status_done()
                    error_name += "URL de requête : " + str(request.input_url) + "\n"
            
            # Enregistrer dans un fichier
            if error_count < 100 : # Ne pas créer trop de fichiers, s'il y a autant d'erreurs, c'est que c'est la même
                file = open( thread_procedure.__name__ + "_number" + str(thread_id) + "_error" + str(error_count) + ".log", "w" )
                file.write( error_name )
                traceback.print_exc( file = file )
            
            # Afficher dans le terminal
            print( error_name )
            traceback.print_exc()
            
            error_count += 1
