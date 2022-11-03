#!/usr/bin/python3
# coding: utf-8

import Pyro5.server
from time import time


"""
Classe représentant une indexation (Nouvelle ou mise à jour) d'un compte
Twitter dans la base de données. Cet objet est le même durant tout le processus
de traitement.

Une requête est identifiée par l'ID du compte Twitter.

Note : Pour les objets, on stocke en réalité l'URI qui mène à l'objet sur le
serveur Pyro, et pas l'objet directement (Car Pyro ne peut pas exécuter sur le
serveur les méthodes des sous-objets), et pas le Proxy vers l'objet (Car un
Proxy ne peut être utilisé que par un seul thread à la fois).
"""
class Scan_Request :
    # Type de requête, pour la reconnaitre plus facilement dans le collecteur
    # d'erreurs
    _request_type = "scan"
    
    """
    @param account_id L'ID du compte Twitter à indexer / scanner. Ne sert qu'à
                      identifier.
    @param acount_name Le nom du compte Twitter à indexer / scanner. Attention,
                       c'est lui qui est revérifié et scanné !
    @param is_prioritary Est ce que cette requête est prioritaire ?
    """
    def __init__ ( self, account_id : int,
                         acount_name : str,
                         is_prioritary : bool = False ) :
        self._account_id = account_id
        self._account_name = acount_name
        self._is_prioritary = is_prioritary
        
        # Si le compte est introuvable
        self._unfound_account = False
        
        # Si jamais un thread de traitement a planté avec la requête, le
        # collecteur d'erreur l'indiquera ici
        self._has_failed = False
        
        # Deux variables de début de traitement de la requête
        # Permet de savoir si, lors d'un éventuel passage de la requête en
        # prioritaire, on doit démonter les files des étapes A et B ou pas
        self._started_SearchAPI_listing = False
        self._started_TimelineAPI_listing = False
        
        # Cache pour les deux listeurs (Etapes A et B)
        # ID dans la liste params.TWITTER_API_KEYS des tokens bloqués par
        # ce compte
        self._blocks_list = []
        
        # Deux variables de fin du traitement de la requête
        # SEULE LE THREAD D'INDEXATION (ETAPE C) A LE DROIT DE METTRE CETTE
        # VALEUR SUR TRUE (Car mettre ces deux valeurs à True autorise
        # l'enregistrement des curseurs)
        self._finished_SearchAPI_indexing = False
        self._finished_TimelineAPI_indexing = False
        
        # Date de début de la procédure
        self._start = time()
        
        # Date de fin de la procédure
        self._finished_date = None
    
    """
    Getters et setters pour Pyro.
    """
    @Pyro5.server.expose
    @property
    def request_type( self ) : return self._request_type
    
    @Pyro5.server.expose
    @property
    def account_id( self ) : return self._account_id
    
    @Pyro5.server.expose
    @property
    def account_name( self ) : return self._account_name
    
    @Pyro5.server.expose
    @property
    def is_prioritary( self ) : return self._is_prioritary
    @Pyro5.server.expose
    @is_prioritary.setter
    def is_prioritary( self, value ) : self._is_prioritary = value
    
    @Pyro5.server.expose
    @property
    def unfound_account( self ) : return self._unfound_account
    @Pyro5.server.expose
    @unfound_account.setter
    def unfound_account( self, value ) : self._unfound_account = value
    
    @Pyro5.server.expose
    @property
    def has_failed( self ) : return self._has_failed
    @Pyro5.server.expose
    @has_failed.setter
    def has_failed( self, value ) : self._has_failed = value
    
    @Pyro5.server.expose
    @property
    def started_SearchAPI_listing( self ) : return self._started_SearchAPI_listing
    @Pyro5.server.expose
    @started_SearchAPI_listing.setter
    def started_SearchAPI_listing( self, value ) : self._started_SearchAPI_listing = value
    
    @Pyro5.server.expose
    @property
    def started_TimelineAPI_listing( self ) : return self._started_TimelineAPI_listing
    @Pyro5.server.expose
    @started_TimelineAPI_listing.setter
    def started_TimelineAPI_listing( self, value ) : self._started_TimelineAPI_listing = value
    
    @Pyro5.server.expose
    @property
    def blocks_list( self ) : return self._blocks_list
    @Pyro5.server.expose
    @blocks_list.setter
    def blocks_list( self, value ) : self._blocks_list = value
    
    @Pyro5.server.expose
    @property
    def finished_SearchAPI_indexing( self ) : return self._finished_SearchAPI_indexing
    @Pyro5.server.expose
    @finished_SearchAPI_indexing.setter
    def finished_SearchAPI_indexing( self, value ) : self._finished_SearchAPI_indexing = value
    
    @Pyro5.server.expose
    @property
    def finished_TimelineAPI_indexing( self ) : return self._finished_TimelineAPI_indexing
    @Pyro5.server.expose
    @finished_TimelineAPI_indexing.setter
    def finished_TimelineAPI_indexing( self, value ) : self._finished_TimelineAPI_indexing = value
    
    @Pyro5.server.expose
    @property
    def start( self ) : return self._start
    
    @Pyro5.server.expose
    @property
    def finished_date( self ) : return self._finished_date
    @Pyro5.server.expose
    @finished_date.setter
    def finished_date( self, value ) : self._finished_date = value
