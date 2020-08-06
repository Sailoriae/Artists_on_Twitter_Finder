#!/usr/bin/python3
# coding: utf-8

import Pyro4

try :
    from class_User_Requests_Pipeline import User_Requests_Pipeline
    from class_Scan_Requests_Pipeline import Scan_Requests_Pipeline
    from class_HTTP_Requests_Limitator import HTTP_Requests_Limitator
except ModuleNotFoundError :
    from .class_User_Requests_Pipeline import User_Requests_Pipeline
    from .class_Scan_Requests_Pipeline import Scan_Requests_Pipeline
    from .class_HTTP_Requests_Limitator import HTTP_Requests_Limitator

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

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
    def __init__ ( self, pyro_port ) :
        # Initialisation du serveur Pyro4
#        Pyro4.config.SERVERTYPE = "multiplex"
        Pyro4.config.THREADPOOL_SIZE = 10000
        Pyro4.config.SERIALIZERS_ACCEPTED = { "pickle" }
        Pyro4.config.SERIALIZER = "pickle"
        self._daemon = Pyro4.Daemon( port = pyro_port )
        
        # Variable pour éteindre tout le système.
        self._keep_service_alive = True
        
        # Variable pour éteindre le serveur Pyro après l'extinction du système
        self._keep_pyro_alive = True
        
        # Pipeline des requêtes des utilisateur.
        self._user_requests = self.register_obj( User_Requests_Pipeline( self ), "user_requests" )
        
        # Pipeline des requêtes d'indexation de comptes Twitter.
        self._scan_requests = self.register_obj( Scan_Requests_Pipeline( self ), "scan_requests" )
        
        # Cache des statistiques, permet de faire moins d'appels à la méthode
        # get_stats().
        bdd_direct_access = SQLite_or_MySQL()
        self._tweets_count, self._accounts_count = bdd_direct_access.get_stats()
        
        # Limitateur du nombre de requêtes sur le serveur HTTP / l'API par
        # secondes
        self._http_limitator = self.register_obj( HTTP_Requests_Limitator(), "http_limitator" )
    
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
    def user_requests( self ) : return Pyro4.Proxy( self._user_requests )
    
    @property
    def scan_requests( self ) : return Pyro4.Proxy( self._scan_requests )
    
    @property
    def tweets_count( self ) : return self._tweets_count
    @tweets_count.setter
    def tweets_count( self, value ) : self._tweets_count = value
    
    @property
    def accounts_count( self ) : return self._accounts_count
    @accounts_count.setter
    def accounts_count( self, value ) : self._accounts_count = value
    
    @property
    def http_limitator( self ) : return Pyro4.Proxy( self._http_limitator )
    
    """
    Lancer le sevreur de mémoire partagée, avec Pyro.
    """
    def launch_pyro_server ( self ) :
        uri = self._daemon.register( self, "shared_memory" )
        print( "URI de la mémoire partagée :", uri )
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
    @param name Le nom à lui donner pour le partage.
    @return L'URI vers cet objet.
    """
    def register_obj ( self, obj, name ) :
        return self._daemon.register( obj, name )
    
    """
    Dé-enregistrer un objet.
    @param L'URI vers cet objet.
    """
    def unregister_obj ( self, uri ) :
        self._daemon.unregister( uri )
