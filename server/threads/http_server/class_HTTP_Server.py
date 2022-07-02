#!/usr/bin/python3
# coding: utf-8

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit
import json
from time import time
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
    change_wdir( "../.." )
    path.append(get_wdir())

from threads.http_server.generate_json import get_user_request_json_model
from threads.http_server.generate_json import generate_user_request_json
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

# Nombre de secondes pendant lesquelles ont garde en cache le JSON retourné par
# l'endpoint GET /stats (Au delà, il sera régénéré)
STATS_CACHE_TTL = 3 # secondes


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
        step_C_index_tweets_queue = scan_requests.step_C_index_tweets_queue
        
        # Envoyer un header "Server" personnalisé
        server_version = "Artists on Twitter Finder"
        sys_version = ""
        
        # Mise en cache
        stats_cache = None # Endpoint GET /stats
        stats_cache_date = 0 # Besoin de rafraichir toutes les STATS_CACHE_TTL secondes
        
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
        
        # Collecteur d'erreurs du traitement des requêtes HTTP
        def do_GET( self, method = "GET" ) :
            try :
                self._do_GET( method = method )
            except Exception as error :
                error_name = "Erreur lors du traitement d'une requête HTTP !\n"
                error_name += f"S'est produite le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')}.\n"
                
                file = open( "http_server_errors.log", "a" )
                file.write( "ICI LE COLLECTEUR D'ERREURS DU SERVEUR HTTP !\n" )
                file.write( "Je suis dans le fichier suivant : threads/http_server/class_HTTP_Server.py\n" )
                file.write( error_name )
                traceback.print_exc( file = file )
                file.write( "\n\n\n" )
                file.close()
                
                print( error_name, end = "" )
                print( f"{type(error).__name__}: {error}" )
                print( "La pile d'appel complète a été écrite dans un fichier." )
                
                # Ne pas chercher à envoyer une erreur 500, on a surement déjà
                # envoyé des données, et peut-être même les headers complets
        
        # Notre méthode GET gère aussi le POST et le HEAD
        def _do_GET( self, method = "GET" ) :
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
            
            # On mettra dans ces variables ce qu'on va retourner
            http_code : int = 200
            response_is_json : bool = False
            response : str = ""
            
            # A partie de maintenant, on fait un "if" puis que des "elif" pour
            # toutes les autres possibilités, puis un "else" final pour le 404
            
            # =================================================================
            # HTTP 429
            # =================================================================
            # Vérifier que l'utilisateur ne fait pas trop de requêtes
            # En premier, c'est plus logique
            # Uniquement pour les API "lourdes" (C'est à dire qui font appel à
            # la mémoire partagée) et qui ne sont pas mises en cache
            # - "/query" en fait partie
            # - "/stats" peut être mise en cache
            # - "/config" est légère
            if ( endpoint not in [ "/stats", "/config" ] and
                 not HTTP_Server.http_limitator.can_request( client_ip ) ) :
                http_code = 429
                response = "429 Too Many Requests\n"
            
            # =================================================================
            # HTTP 414
            # =================================================================
            # Vérifier la longueur de l'URL de requête, pour éviter que des
            # petits malins viennent nous innonder notre mémoire vive
            elif len( self.path ) > MAX_URI_LENGTH :
                http_code = 414
                response = "414 Request-URI Too Long\n"
            
            # =================================================================
            # HTTP 413
            # =================================================================
            # Vérifier la taille du contenu de la requête, pour éviter que des
            # petits malins viennent nous innonder notre mémoire vive
            elif method == "POST" and content_length > MAX_CONTENT_LENGTH :
                http_code = 413
                response = "413 Payload Too Large\n"
            
            # =================================================================
            # HTTP 200
            # =================================================================
            # Racine de l'API, affiche juste un petit message
            # GET /
            elif endpoint == "/" :
                http_code = 200
                response = "Artists of Twitter Finder\n"
                response += "Vous êtes sur l'API d'AOTF. Merci de consulter sa documentation afin de l'utiliser.\n"
                response += "You are on the AOTF API. Please check its documentation to use it.\n"
            
            # Si on veut lancer une requête ou obtenir son résultat
            # GET /query
            # GET /query?url=[URL de l'illustration de requête]
            elif endpoint == "/query" :
                http_code = 200
                response_dict = get_user_request_json_model()
                
                illust_url = None
                if method == "POST" :
                    if content_length != 0 :
                        try :
                            illust_url = self.rfile.read(content_length).decode('utf-8')
                        except UnicodeDecodeError :
                            response_dict["status"] = "END"
                            response_dict["error"] = "NOT_AN_URL"
                else :
                    try :
                        illust_url = parameters["url"][0]
                    except KeyError :
                        pass
                
                # On envoit forcément les mêmes champs, même si ils sont vides !
                if illust_url == None :
                    if response_dict["error"] == None :
                        response_dict["status"] = "END"
                        response_dict["error"] = "NO_URL_FIELD"
                
                elif len( illust_url ) > MAX_ILLUST_URL_SIZE :
                    response_dict["status"] = "END"
                    response_dict["error"] = "URL_TOO_LONG"
                
                else :
                    # Lance une nouvelle requête, ou donne la requête déjà existante
                    request = HTTP_Server.user_requests.launch_request( illust_url,
                                                                        ip_address = client_ip )
                    
                    # Si request == None, c'est qu'on ne peut pas lancer une
                    # nouvelle requête car l'adresse IP a trop de requêtes en
                    # cours de traitement, donc on renvoit l'erreur
                    # YOUR_IP_HAS_MAX_PROCESSING_REQUESTS
                    if request == None :
                        response_dict["status"] = "END"
                        response_dict["error"] = "YOUR_IP_HAS_MAX_PROCESSING_REQUESTS"
                    
                    # Sinon, on envoit les informations sur la requête
                    else :
                        generate_user_request_json( request, response_dict )
                
                response = json.dumps( response_dict )
                response_is_json = True
            
            # Si on demande les stats
            # GET /stats
            elif endpoint == "/stats" :
                http_code = 200
                
                if ( HTTP_Server.stats_cache == None or
                     time() - HTTP_Server.stats_cache_date >= STATS_CACHE_TTL ) :
                    HTTP_Server.stats_cache = json.dumps({
                        "indexed_tweets_count" : HTTP_Server.shared_memory.tweets_count,
                        "indexed_accounts_count" : HTTP_Server.shared_memory.accounts_count,
                        "processing_user_requests_count" : HTTP_Server.user_requests.processing_requests_count,
                        "processing_scan_requests_count" : HTTP_Server.scan_requests.processing_requests_count,
                        "pending_tweets_count" : HTTP_Server.step_C_index_tweets_queue.qsize()
                    })
                    HTTP_Server.stats_cache_date = time()
                
                response = HTTP_Server.stats_cache
                response_is_json = True
            
            # Si on demande les informations sur le serveur
            # GET /config
            elif endpoint == "/config" :
                http_code = 200
                
                # Ne peut pas être mis en cache car dépend de l'adresse IP
                response_dict = {
                    "limit_per_ip_address" : param.MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS,
                    "ip_can_bypass_limit" : client_ip in param.UNLIMITED_IP_ADDRESSES,
                    "update_accounts_frequency" : param.DAYS_WITHOUT_UPDATE_TO_AUTO_UPDATE,
                    "max_uri_length" : MAX_URI_LENGTH,
                    "max_content_length" : MAX_CONTENT_LENGTH,
                    "max_illust_url_size" : MAX_ILLUST_URL_SIZE
                }
                
                response = json.dumps( response_dict )
                response_is_json = True
            
            # =================================================================
            # HTTP 404
            # =================================================================
            # Sinon, page inconnue, erreur 404
            else :
                http_code = 404
                response = "404 Not Found\n"
            
            # Envoyer la réponse
            self.send_response(http_code)
            if response_is_json :
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
            else :
                self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write( response.encode("utf-8") )
            
            print( "[HTTP]", client_ip, self.log_date_time_string(), method, self.path, "HTTP", http_code )
    
    return HTTP_Server
