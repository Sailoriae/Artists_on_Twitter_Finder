#!/usr/bin/python3
# coding: utf-8

import Pyro4
from time import sleep


"""
Objet pour passer des messages aux processus fils du serveur AOTF.
"""
@Pyro4.expose
class Processes_Registry :
    def __init__ ( self, root_shared_memory ) :
        self._root = root_shared_memory
        
        # Liste des PID des processus fils
        self._pids = []
        
        # Dictionnaire pour passer l'ordre d'écriture des piles d'exécution
        # Permet d'associer le PID du processus avec un booléen notant si il
        # doit recevoir cet ordre (True si il doit, False sinon)
        # Pas besoin d'un sémaphore, le GIL fait son travail
        self._write_stacks = {}
    
    """
    Enregistrer un processus fils du serveur AOTF.
    @param pid PID du processus fils.
    """
    def register_process ( self, pid : int ) -> None:
        if pid in self._pids :
            raise AssertionError( f"Le processus {pid} a déjà été enregistré !" )
        self._pids.append( int(pid) )
    
    """
    Donner aux processus fils l'ordre d'écriture des piles d'appels de leurs
    threads qu'ils éxécutent.
    """
    def write_stacks ( self ) -> None :
        for pid in self._pids :
            self._write_stacks[ int(pid) ] = True
    
    """
    Obtention d'un message. Contient les temps d'attente.
    Cette fonction dure au maximum 1 minute avant de retourner None
    @param pid PID du processus fils.
    """
    def get_message ( self, pid : int ) -> str :
        iteration = 0
        while self._root.keep_threads_alive :
            iteration += 1
            
            if int(pid) in self._write_stacks :
                if self._write_stacks[ int(pid) ] :
                    self._write_stacks[ int(pid) ] = False
                    return "write_stacks"
            
            sleep( 3 )
            if iteration >= 20 : # Maximum 1 minute
                return None