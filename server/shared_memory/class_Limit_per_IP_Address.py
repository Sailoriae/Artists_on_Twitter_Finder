#!/usr/bin/python3
# coding: utf-8

import Pyro4
import threading

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
    change_wdir( ".." )
    path.append(get_wdir())

import parameters as param


"""
Classe de gestion des adresses IP de requête.
Permet de limiter le nombre de requêtes en cours de traitement par adresse IP.
"""
@Pyro4.expose
class Limit_per_IP_Address :
    def __init__ ( self ) :
        # Dictionnaire contenant le nombre de requêtes en cours de traitement
        # par adresse IP.
        self._dict_of_ip_addresses = {}
        
        # Sémaphore d'accès au dictionnaire précédente.
        self._dict_of_ip_addresses_sem = threading.Semaphore()
    
    """
    Faire +1 au nombre de requête en cours de traitement pour une adresse IP.
    
    @param ip_address L'adresse IP concernée.
    @return True si on a pu faire +1.
            False si l'adresse IP a atteint son nombre maximum de requêtes en
            cours de traitement.
    """
    def add_ip_address ( self, ip_address : str ) -> bool :
        if ip_address in param.UNLIMITED_IP_ADDRESSES :
            return True
        
        self._dict_of_ip_addresses_sem.acquire()
        try :
            current_count = self._dict_of_ip_addresses[ ip_address ]
        except KeyError :
            self._dict_of_ip_addresses[ ip_address ] = 1
            self._dict_of_ip_addresses_sem.release()
            return True
        
        else :
            if current_count < param.MAX_PROCESSING_REQUESTS_PER_IP_ADDRESS :
                self._dict_of_ip_addresses[ ip_address ] = current_count + 1
                self._dict_of_ip_addresses_sem.release()
                return True
            else :
                self._dict_of_ip_addresses_sem.release()
                return False
    
    """
    Faire -1 au nombre de requêtes en cours de traitement pour une adresse IP.
    
    @param ip_address L'adresse IP à concernée.
    """
    def remove_ip_address ( self, ip_address : str ) :
        self._dict_of_ip_addresses_sem.acquire()
        try :
            current_count = self._dict_of_ip_addresses[ ip_address ]
        except KeyError :
            pass
        else :
            self._dict_of_ip_addresses[ ip_address ] = current_count - 1
        self._dict_of_ip_addresses_sem.release()
