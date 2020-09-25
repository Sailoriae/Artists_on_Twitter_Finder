#!/usr/bin/python3
# coding: utf-8

from datetime import datetime

# Ajouter le répertoire parent du parent au PATH pour pouvoir importer
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

import parameters as param


"""
Itérateur sur les comptes dans la base de données, triés dans l'ordre du moins
récemment mise à jour au plus récemment mis à jour.
"""
class Less_Recently_Updated_Accounts_Iterator :
    def __init__( self, cursor ) :
        self.cursor = cursor

    def __iter__( self ) :
        return self

    """
    @return Un triplet contenant :
            - L'ID du compte Twitter,
            - Sa date de dernière MàJ avec l'API de recherche,
            - Et sa date dernière MàJ avec l'API de timeline.
    """
    def __next__( self ) :
        triplet = self.cursor.fetchone()
        if triplet == None :
            raise StopIteration
        last_SearchAPI_indexing_local_date = triplet[1]
        last_TimelineAPI_indexing_local_date = triplet[2]
        if last_SearchAPI_indexing_local_date != None :
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
                last_SearchAPI_indexing_local_date = datetime.strptime( last_SearchAPI_indexing_local_date, '%Y-%m-%d %H:%M:%S' )
        if last_TimelineAPI_indexing_local_date != None :
            if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
                last_TimelineAPI_indexing_local_date = datetime.strptime( last_TimelineAPI_indexing_local_date, '%Y-%m-%d %H:%M:%S' )
        return ( triplet[0], last_SearchAPI_indexing_local_date, last_TimelineAPI_indexing_local_date )
