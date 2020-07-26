#!/usr/bin/python3
# coding: utf-8

import threading

# Ajouter le répertoire parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))

import parameters as param


"""
Classe de gestion des adresses IP de requête.
Permet de limiter le nombre de requêtes en cours de traitement par adresse IP.
"""
class Limit_per_IP_Address :
    def __init__ ( self ) :
        # Dictionnaire contenant le nombre de requêtes en cours de traitement
        # par adresse IP.
        self.dict_of_ip_addresses = {}
        
        # Sémaphore d'accès au dictionnaire précédente.
        self.dict_of_ip_addresses_sem = threading.Semaphore()
    
    """
    Faire +1 au nombre de requête en cours de traitement pour une addresse IP.
    
    @param ip_address L'adresse IP concernée.
    @return True si on a pu faire +1.
            False si l'addresse IP a atteint son nombre maximum de requêtes en
            cours de traitement.
    """
    def add_ip_address ( self, ip_address : str ) -> bool :
        if ip_address in param.UNLIMITED_IP_ADDRESSES :
            return True
        
        self.dict_of_ip_addresses_sem.acquire()
        try :
            current_count = self.dict_of_ip_addresses[ ip_address ]
        except KeyError :
            self.dict_of_ip_addresses[ ip_address ] = 1
            self.dict_of_ip_addresses_sem.release()
            return True
        
        else :
            if current_count < param.MAX_PENDING_REQUESTS_PER_IP_ADDRESS :
                self.dict_of_ip_addresses[ ip_address ] = current_count + 1
                self.dict_of_ip_addresses_sem.release()
                return True
            else :
                self.dict_of_ip_addresses_sem.release()
                return False
    
    """
    Faire -1 au nombre de requêtes en cours de traitement pour une addresse IP.
    
    @param ip_address L'adresse IP à concernée.
    """
    def remove_ip_address ( self, ip_address : str ) :
        self.dict_of_ip_addresses_sem.acquire()
        try :
            current_count = self.dict_of_ip_addresses[ ip_address ]
        except KeyError :
            pass
        else :
            self.dict_of_ip_addresses[ ip_address ] = current_count - 1
        self.dict_of_ip_addresses_sem.release()
