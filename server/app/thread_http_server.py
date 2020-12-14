#!/usr/bin/python3
# coding: utf-8

from http.server import ThreadingHTTPServer

try :
    from class_HTTP_Server import http_server_container
except ModuleNotFoundError :
    from .class_HTTP_Server import http_server_container

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param


"""
ATTENTION ! CE THREAD DOIT ETRE UNIQUE !

Thread du serveur HTTP.

Codes sources pour comprendre :
https://github.com/python/cpython/blob/3.9/Lib/http/server.py
https://github.com/python/cpython/blob/3.9/Lib/socketserver.py
"""
def thread_http_server( thread_id : int, shared_memory ) :
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
