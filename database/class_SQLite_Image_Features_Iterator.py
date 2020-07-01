#!/usr/bin/python3
# coding: utf-8

import sqlite3

try :
    from class_Image_in_DB import Image_in_DB
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_Image_in_DB import Image_in_DB


"""
Itérateur sur les images de Tweets contenues dans la base de données.

Cet objet doit uniquement être instancié par la méthode
"get_images_in_db_iterator()" de la classe "SQLite" contenue dans le fichier
"class_SQLite.py".
"""
class SQLite_Image_Features_Iterator :
    def __init__( self, cursor : sqlite3.Cursor ) :
        self.cursor : sqlite3.Cursor = cursor

    def __iter__( self ) :
        return self

    """
    @return Un objet Image_in_DB
    """
    def __next__( self ) -> Image_in_DB:
        line = self.cursor.fetchone()
        if line == None :
            raise StopIteration
        return Image_in_DB( line[0],
                            line[1],
                            [ float(value) for value in line[2].split(';') ] )
