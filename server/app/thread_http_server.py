#!/usr/bin/python3
# coding: utf-8

from http.server import ThreadingHTTPServer

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
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

from app.class_HTTP_Server import http_server_container
import parameters as param


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Thread du serveur HTTP.

Codes sources pour comprendre :
https://github.com/python/cpython/blob/3.9/Lib/http/server.py
https://github.com/python/cpython/blob/3.9/Lib/socketserver.py
"""
def thread_http_server( thread_id : int, shared_memory ) :
    # Sécurité, vérifier que le thread est unique
    if thread_id != 1 :
        raise AssertionError( "Ce thread doit être unique, et doit pas conséquent avoir 1 comme identifiant (\"thread_id\") !" )
    
    # Obtenir la classe du serveur HTTP
    HTTP_Server = http_server_container( shared_memory.get_URI() )
    
    # http.server.ThreadingHTTPServer() fait lui-même le multi-threads du
    # serveur HTTP
    http_server = ThreadingHTTPServer( ("", param.HTTP_SERVER_PORT ), HTTP_Server )
    
    # Le timeour doit être définit ici, et non dans la classe HTTP_Server, car
    # handle_request() est définit dans l'arbre de ThreadingHTTPServer, et non
    # dans celui de HTTP_Server -> BaseHTTPRequestHandler
    http_server.timeout = 5 # Fonctionne car handle_request() sort lors du stop
    
    while shared_memory.keep_service_alive :
        # Ordre des appels :
        # - handle_request() <== Permet le respect de http_server.timeout, alors que serve_forever() ne le respecte pas
        # - _handle_request_noblock()
        # - process_request() <== Rédéfinit par ThreadingMixIn dont ThreadingHTTPServer est fille, démarre un Thread
        # - process_request_thread()
        # ...
        http_server.handle_request()
    http_server.server_close()
    
    print( f"[http_server_th{thread_id}] Arrêté !" )
    return
