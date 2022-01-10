#!/usr/bin/python3
# coding: utf-8

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit
import json

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

from threads.user_pipeline.generate_json import get_user_request_json_model
from threads.user_pipeline.generate_json import generate_user_request_json
import parameters as param
from shared_memory.open_proxy import open_proxy


# Taille maximale de l'URI de la requête (Sinon, HTTP 414)
# Cela contient aussi les paramètres
MAX_URI_LENGTH = 512 # caractères

# Taille maximale du contenu d'une requête POST (Sinon, HTTP 413)
MAX_CONTENT_LENGTH = 1024 # octets

# Taille maximale de l'URL d'un illustration (Sinon, "URL_TOO_LONG")
# On sépare pour permettre une potentielle autre utilisation du POST
MAX_ILLUST_URL_SIZE = 256 # caractères


"""
Serveur HTTP, permettant d'utiliser AOTF.

Note : NE PAS CREER UNE API PERMETTANT DE FAIRE UNE RECHERCHE DANS TOUTE LA
BASE DE DONNEES ! En effet, malgré la vitesse améliorée par la méthode de la
recherche exacte, elle est toujours trop lente pour les très grosses BDD, et
donc peut être utilisé à des fins de DDOS.
De plus, cela serait une grosse faille de sécurité. Voir ce que sont les
"Server side request forgery" (SSRF).
"""
# Fonction contenant la classe, permettant de passer le paramètre shared_memory
def http_server_container ( shared_memory_uri_arg ) :
    class HTTP_Server( BaseHTTPRequestHandler ) :
        # Pyro permet de partager un Proxy entre threads, et un thread est
        # créé à chaque requête HTTP, avec cet objet, et est détruit à la fin
        # de la requête.
        # On peut donc garder en attribut de classe des proxies vers la mémoire
        # partagée. Cela permet de ne pas ouvrir un proxy à chaque requête.
        shared_memory = open_proxy( shared_memory_uri_arg )
        http_limitator = shared_memory.http_limitator
        user_requests = shared_memory.user_requests
        scan_requests = shared_memory.scan_requests
        step_C_index_account_tweets_queue = scan_requests.step_C_index_account_tweets_queue
        
        # Envoyer un header "Server" personnalisé
        server_version = "Artists on Twitter Finder"
        sys_version = ""
        
        def __init__( self, *args, **kwargs ) :
            super(BaseHTTPRequestHandler, self).__init__(*args, **kwargs)
        
        # Ne pas afficher les logs par défaut dans la console
        def log_message( self, format, *args ) :
            return
        
        # La méthode POST fonctionne comme la méthode GET
        def do_POST( self ) :
            return self.do_GET( method = "POST" )
        
        # La méthode HEAD doit fonctionner comme la méthode GET
        # Elle n'envoit juste pas de corps
        def do_HEAD( self ) :
            return self.do_GET( method = "HEAD" )
        
        def do_GET( self, method = "GET" ) :
            # Analyser le chemin du GET HTTP
            endpoint = urlsplit( self.path ).path
            parameters = dict( parse_qs( urlsplit( self.path ).query ) )
            
            client_ip = self.headers["X-Forwarded-For"]
            if client_ip == None :
                client_ip = self.client_address[0]
            
            # Obtenir la taille du contenu (Dans le cas d'une requête POST)
            if method == "POST" :
                # Le param "Content-Length" est insensible à la casse
                content_length = int(self.headers.get("Content-Length", 0))
            
            # A partie de maintenant, on fait un "if" puis que des "elif" pour
            # toutes les autres possibilités, puis un "else" final pour le 404
            
            # =================================================================
            # HTTP 429
            # =================================================================
            # Vérifier que l'utilisateur ne fait pas trop de requêtes
            # En premier, c'est plus logique
            if not self.http_limitator.can_request( client_ip ) :
                http_code = 429
                self.send_response(http_code)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                
                self.wfile.write( "429 Too Many Requests\n".encode("utf-8") )
            
            # =================================================================
            # HTTP 414
            # =================================================================
            # Vérifier la longueur de l'URL de requête, pour éviter que des
            # petits malins viennent nous innonder notre mémoire vive
            elif len( self.path ) > MAX_URI_LENGTH :
                http_code = 414
                self.send_response(http_code)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                
                self.wfile.write( "414 Request-URI Too Long\n".encode("utf-8") )
            
            # =================================================================
            # HTTP 413
            # =================================================================
            # Vérifier la taille du contenu de la requête, pour éviter que des
            # petits malins viennent nous innonder notre mémoire vive
            elif method == "POST" and content_length > MAX_CONTENT_LENGTH :
                http_code = 413
                self.send_response(http_code)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                
                self.wfile.write( "413 Payload Too Large\n".encode("utf-8") )
            
            # =================================================================
            # HTTP 200
            # =================================================================
            # Racine de l'API, affiche juste un petit message
            # GET /
            elif endpoint == "/" :
                http_code = 200
                self.send_response(http_code)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                
                to_send = "Artists of Twitter Finder\n"
                to_send += "Vous êtes sur l'API d'AOTF. Merci de consulter sa documentation afin de l'utiliser.\n"
                to_send += "You are on the AOTF API. Please check its documentation to use it.\n"
                
                self.wfile.write( to_send.encode("utf-8") )
            
            # Si on veut lancer une requête ou obtenir son résultat
            # GET /query
            # GET /query?url=[URL de l'illustration de requête]
            elif endpoint == "/query" :
                http_code = 200
                self.send_response(http_code)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                response_dict = get_user_request_json_model()
                
                illust_url = None
                if method == "POST" :
                    if content_length != 0 :
                        illust_url = self.rfile.read(content_length).decode('utf-8')
                else :
                    try :
                        illust_url = parameters["url"][0]
                    except KeyError :
                        pass
                
                # On envoit forcément les mêmes champs, même si ils sont vides !
                if illust_url == None :
                    response_dict["status"] = "END"
                    response_dict["error"] = "NO_URL_FIELD"
                
                elif len( illust_url ) > MAX_ILLUST_URL_SIZE :
                    response_dict["status"] = "END"
                    response_dict["error"] = "URL_TOO_LONG"
                
                else :
                    # Lance une nouvelle requête, ou donne la requête déjà existante
                    request = self.user_requests.launch_request( illust_url,
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
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                response_dict = {
                    "indexed_tweets_count" : self.shared_memory.tweets_count,
                    "indexed_accounts_count" : self.shared_memory.accounts_count,
                    "processing_user_requests_count" : self.user_requests.processing_requests_count,
                    "processing_scan_requests_count" : self.scan_requests.processing_requests_count,
                    "pending_tweets_count" : self.step_C_index_account_tweets_queue.qsize()
                }
                
                json_text = json.dumps( response_dict )
                self.wfile.write( json_text.encode("utf-8") )
            
            # Si on demande les informations sur le serveur
            # GET /config
            elif endpoint == "/config" :
                http_code = 200
                self.send_response(http_code)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                response_dict = {
                    "limit_per_ip_address" : param.MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS,
                    "update_accounts_frequency" : param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE,
                    "max_uri_length" : MAX_URI_LENGTH,
                    "max_content_length" : MAX_CONTENT_LENGTH,
                    "max_illust_url_size" : MAX_ILLUST_URL_SIZE
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
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                
                self.wfile.write( "404 Not Found\n".encode("utf-8") )
            
            print( "[HTTP]", client_ip, self.log_date_time_string(), method, self.path, "HTTP", http_code )
    
    return HTTP_Server
