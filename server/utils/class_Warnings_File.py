#!/usr/bin/python3
# coding: utf-8

from datetime import datetime


"""
Classe du ficher d'avertissements. Il permet à n'importe quel composant du
serveur AOTF de journaliser quelque part des informations importantes qu'on
pourrait rater dans l'interface en ligne de commande.
"""
class Warnings_File :
    def __init__ ( self ) :
        self._file = open( "warnings.log", "a" )
    
    def write ( self, line ) :
        self._file.write( datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ") + line + "\n" )
    
    def close ( self ) :
        if not self._file.closed :
            self._file.close()
    
    def __del__ ( self ) :
        self.close()
