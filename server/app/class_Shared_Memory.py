#!/usr/bin/python3
# coding: utf-8

try :
    from class_User_Requests_Pipeline import User_Requests_Pipeline
    from class_Scan_Requests_Pipeline import Scan_Requests_Pipeline
except ModuleNotFoundError :
    from .class_User_Requests_Pipeline import User_Requests_Pipeline
    from .class_Scan_Requests_Pipeline import Scan_Requests_Pipeline

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param
from tweet_finder.database import SQLite_or_MySQL
from tweet_finder.twitter import TweepyAbtraction


"""
Mémoire partagée entre les threads, à initialiser une seule fois !
"""
class Shared_Memory :
    def __init__ ( self ) :
        # Variable pour éteindre tout le système.
        self.keep_service_alive = True
        
        # Pipeline des requêtes des utilisateur.
        self.user_requests = User_Requests_Pipeline()
        
        # Pipeline des requêtes d'indexation de comptes Twitter.
        self.scan_requests = Scan_Requests_Pipeline()
        
        # Cache des statistiques, permet de faire moins d'appels à la méthode
        # get_stats().
        bdd_direct_access = SQLite_or_MySQL()
        self.tweets_count, self.accounts_count = bdd_direct_access.get_stats()
        
        # Initialisation d'une couche d'abstraction à l'API Twitter
        # Peut être utilisé par les threads
        self.twitter = TweepyAbtraction( param.API_KEY,
                                         param.API_SECRET,
                                         param.OAUTH_TOKEN,
                                         param.OAUTH_TOKEN_SECRET )
