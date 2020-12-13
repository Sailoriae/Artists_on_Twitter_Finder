#!/usr/bin/python3
# coding: utf-8

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit
import json

try :
    from user_pipeline import get_user_request_json_model, generate_user_request_json
except ModuleNotFoundError :
    from .user_pipeline import get_user_request_json_model, generate_user_request_json

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from shared_memory.open_proxy import open_proxy


"""
Serveur HTTP
"""
# Fonction contenant la classe, permettant de passer le paramètre shared_memory
def http_server_container ( shared_memory_uri_arg ) :
    class HTTP_Server( BaseHTTPRequestHandler ) :
        shared_memory_uri = shared_memory_uri_arg # Attribut de classe
        
        def __init__( self, *args, **kwargs ) :
            self.shared_memory = open_proxy( self.shared_memory_uri )
            super(BaseHTTPRequestHandler, self).__init__(*args, **kwargs)
        
        # Ne pas afficher les logs par défaut dans la console
        def log_message( self, format, *args ) :
            return
        
        def do_GET( self ) :
            # Analyser le chemin du GET HTTP
            endpoint = urlsplit( self.path ).path
            parameters = dict( parse_qs( urlsplit( self.path ).query ) )
            
            client_ip = self.headers["X-Forwarded-For"]
            if client_ip == None :
                client_ip = self.client_address[0]
            
            # A partie de maintenant, on fait un "if" puis que des "elif" pour
            # toutes les autres possibilités, puis un "else" final pour le 404
            
            # =================================================================
            # HTTP 414
            # =================================================================
            # Vérifier la longueur de l'URL de requête, pour éviter que des
            # petits malins viennent nous innonder notre mémoire vive
            if len( self.path ) > 200 :
                http_code = 414
                self.send_response(http_code)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                
                self.wfile.write( "414 Request-URI Too Long\n".encode("utf-8") )
            
            # =================================================================
            # HTTP 429
            # =================================================================
            # Vérifier que l'utilisateur ne fait pas trop de requêtes
            elif not self.shared_memory.http_limitator.can_request( client_ip ) :
                http_code = 429
                self.send_response(http_code)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                
                self.wfile.write( "429 Too Many Requests\n".encode("utf-8") )
            
            # =================================================================
            # HTTP 200
            # =================================================================
            # Si on veut lancer une requête ou obtenir son résultat
            # GET /query
            # GET /query?url=[URL de l'illustration de requête]
            elif endpoint == "/query" :
                http_code = 200
                self.send_response(http_code)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                response_dict = get_user_request_json_model()
                
                # On envoit forcément les mêmes champs, même si ils sont vides !
                try :
                    illust_url = parameters["url"][0]
                except KeyError :
                    response_dict["status"] = "END"
                    response_dict["error"] = "NO_URL_FIELD"
                else :
                    # Lance une nouvelle requête, ou donne la requête déjà existante
                    request = self.shared_memory.user_requests.launch_request( illust_url,
                                                                               ip_address = client_ip )
                    
                    # Si request == None, c'est qu'on ne peut pas lancer une
                    # nouvelle requête car l'addresse IP a trop de requêtes en
                    # cours de traitement, donc on renvoit l'erreur
                    # YOUR_IP_HAS_MAX_PROCESSING_REQUESTS
                    if request == None :
                        response_dict["status"] = "END"
                        response_dict["error"] = "YOUR_IP_HAS_MAX_PROCESSING_REQUESTS"
                    
                    # Sinon, on envoit les informations sur la requête
                    else :
                        generate_user_request_json( request, response_dict )
                
                json_text = json.dumps( response_dict )
                self.wfile.write( json_text.encode("utf-8") )
            
            # Si on demande les stats
            # GET /stats
            elif endpoint == "/stats" :
                http_code = 200
                self.send_response(http_code)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                response_dict = {
                    "indexed_tweets_count" : self.shared_memory.tweets_count,
                    "indexed_accounts_count" : self.shared_memory.accounts_count,
                    "processing_user_requests_count" : self.shared_memory.user_requests.processing_requests_count,
                    "processing_scan_requests_count" : self.shared_memory.scan_requests.processing_requests_count,
                    "limit_per_ip_address" : param.MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS,
                    "update_accounts_frequency" : param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE
                }
                
                json_text = json.dumps( response_dict )
                self.wfile.write( json_text.encode("utf-8") )
            
            # =================================================================
            # HTTP 404
            # =================================================================
            # Sinon, page inconnue, erreur 404
            else :
                http_code = 404
                self.send_response(http_code)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                
                self.wfile.write( "404 Not Found\n".encode("utf-8") )
            
            print( "[HTTP]", client_ip, self.log_date_time_string(), "GET", self.path, "HTTP", http_code )
    
    return HTTP_Server
