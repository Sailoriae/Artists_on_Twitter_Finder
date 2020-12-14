#!/usr/bin/python3
# coding: utf-8

import Pyro4

try :
    from class_User_Requests_Pipeline import User_Requests_Pipeline
    from class_Scan_Requests_Pipeline import Scan_Requests_Pipeline
    from class_HTTP_Requests_Limitator import HTTP_Requests_Limitator
    from class_Metrics_Container import Metrics_Container
    from class_Threads_Registry import Threads_Registry
    from open_proxy import open_proxy
except ModuleNotFoundError :
    from .class_User_Requests_Pipeline import User_Requests_Pipeline
    from .class_Scan_Requests_Pipeline import Scan_Requests_Pipeline
    from .class_HTTP_Requests_Limitator import HTTP_Requests_Limitator
    from .class_Metrics_Container import Metrics_Container
    from .class_Threads_Registry import Threads_Registry
    from .open_proxy import open_proxy

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from tweet_finder.database import SQLite_or_MySQL


"""
Mémoire partagée entre les threads, à initialiser une seule fois !

Note : Pour les objets, on stocke en réalité l'URI qui mène à l'objet sur le
serveur Pyro, et pas l'objet directement (Car Pyro ne peut pas exécuter sur le
serveur les méthodes des sous-objets), et pas le Proxy vers l'objet (Car un
Proxy ne peut être utilisé que par un seul thread à la fois).
"""
@Pyro4.expose
class Shared_Memory :
    """
    @param pyro_port Port du serveur Pyro.
    @param pool_size Nombre de threads ouvrables au maxmimum. Sachant qu'un
                     thread est créé à chaque connexion. On doit donc autoriser
                     beaucoup de connexions en même temps !
                     Donc mettre un très grand nombre (De l'ordre de 10^4).
                     Ce nombre doit être proportionnel aux nombre de threads
                     de traitement, sachant qu'ils peuvent ouvrir chacun plus
                     de 1 000 proxies !
                     De plus, ce nombre doit être égal au nombre maximum
                     autorisé de descripteurs de fichiers.
    """
    def __init__ ( self, pyro_port, pool_size ) :
        # Initialisation du serveur Pyro4
        if param.ENABLE_MULTIPROCESSING :
            Pyro4.config.THREADPOOL_SIZE = pool_size
            Pyro4.config.SERIALIZERS_ACCEPTED = { "pickle" }
            Pyro4.config.SERIALIZER = "pickle"
            self._daemon = Pyro4.Daemon( port = pyro_port )
        
        # Variable pour éteindre tout le système.
        self._keep_service_alive = True
        
        # Variable pour éteindre le serveur Pyro après l'extinction du système
        self._keep_pyro_alive = True
        
        # Pipeline des requêtes des utilisateur.
        self._user_requests = self.register_obj( User_Requests_Pipeline( self ) )
        
        # Pipeline des requêtes d'indexation de comptes Twitter.
        self._scan_requests = self.register_obj( Scan_Requests_Pipeline( self ) )
        
        # Cache des statistiques, permet de faire moins d'appels à la méthode
        # get_stats().
        bdd_direct_access = SQLite_or_MySQL()
        self._tweets_count, self._accounts_count = bdd_direct_access.get_stats()
        
        # Limitateur du nombre de requêtes sur le serveur HTTP / l'API par
        # secondes
        self._http_limitator = self.register_obj( HTTP_Requests_Limitator() )
        
        # Conteneur des mesures de temps d'éxécution.
        self._execution_metrics = self.register_obj( Metrics_Container() )
        
        # Objet où les threads s'enregistrent.
        # Ils y mettent aussi leur requête en cours de traitement, afin que
        # leurs collecteurs d'erreurs mettent ces  requêtes en échec lors d'un
        # plantage.
        # Les threads sont identifiés par la chaine suivante :
        # f"{thread_procedure.__name__}_number{thread_id}"
        self._threads_registry = self.register_obj( Threads_Registry() )
        
        # Communication entre le thread de reset des curseur d'indexation avec
        # l'API de recherche ("thread_reset_SearchAPI_cursors"), et celui de
        # MàJ automatique de l'indexation des comptes présents dans la BDD
        # ("thread_auto_update_accounts")
        self._force_auto_update_reloop = False
    
    """
    Getters et setters pour Pyro.
    """
    @property
    def keep_service_alive( self ) : return self._keep_service_alive
    @keep_service_alive.setter
    def keep_service_alive( self, value ) : self._keep_service_alive = value
    
    @property
    def keep_pyro_alive( self ) : return self._keep_pyro_alive
    @keep_pyro_alive.setter
    def keep_pyro_alive( self, value ) : self._keep_pyro_alive = value
    
    @property
    def user_requests( self ) : return open_proxy( self._user_requests )
    
    @property
    def scan_requests( self ) : return open_proxy( self._scan_requests )
    
    @property
    def tweets_count( self ) : return self._tweets_count
    @tweets_count.setter
    def tweets_count( self, value ) : self._tweets_count = value
    
    @property
    def accounts_count( self ) : return self._accounts_count
    @accounts_count.setter
    def accounts_count( self, value ) : self._accounts_count = value
    
    @property
    def http_limitator( self ) : return open_proxy( self._http_limitator )
    
    @property
    def execution_metrics( self ) : return open_proxy( self._execution_metrics )
    
    @property
    def threads_registry( self ) : return open_proxy( self._threads_registry )
    
    @property
    def force_auto_update_reloop( self ) : return self._force_auto_update_reloop
    @force_auto_update_reloop.setter
    def force_auto_update_reloop( self, value ) : self._force_auto_update_reloop = value
    
    """
    Lancer le sevreur de mémoire partagée, avec Pyro.
    """
    def launch_pyro_server ( self ) :
        if not param.ENABLE_MULTIPROCESSING :
            raise RuntimeError( "Multiprocessing désactivé, le serveur Pyro ne peut pas être démarré !" )
        uri = self._daemon.register( self, "shared_memory" )
        print( f"URI de la mémoire partagée : {uri}" )
        self._daemon.requestLoop( loopCondition = self.keep_running )
    
    """
    Getter pour éteindre le serveur Pyro.
    """
    def keep_running ( self ) :
        return self._keep_pyro_alive
    
    """
    Partager un objet. A appeler à chaque fois que la mémoire partagée
    crée un objet !
    
    @param obj L'objet Python à partager.
    @return L'URI vers cet objet, sous la forme d'une string.
    """
    def register_obj ( self, obj ) :
        if param.ENABLE_MULTIPROCESSING :
            return self._daemon.register( obj ).asString()
        else :
            return obj
    
    """
    Dé-enregistrer un objet.
    @param L'URI vers cet objet.
    """
    def unregister_obj ( self, uri ) :
        if param.ENABLE_MULTIPROCESSING :
            self._daemon.unregister( uri )
