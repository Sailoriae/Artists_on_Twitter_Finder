#!/usr/bin/python3
# coding: utf-8

try :
    from class_Image_in_DB import Image_in_DB
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_Image_in_DB import Image_in_DB

CBIR_LIST_LENGHT = 240


"""
Itérateur sur les images de Tweets contenues dans la base de données.

Cet objet doit uniquement être instancié par la méthode
"get_images_in_db_iterator()" de la classe "SQLite_or_MySQL" contenue dans le
fichier "class_SQLite_or_MySQL.py".
"""
class Image_Features_Iterator :
    """
    @param 4 curseurs sur les 4 tables d'images.
    """
    def __init__( self, c_1, c_2, c_3, c_4 ) :
        self.current_cursor = 1
        self.cursors = [ None, c_1, c_2, c_3, c_4 ]

    def __iter__( self ) :
        return self

    """
    @return Un objet Image_in_DB
    """
    def __next__( self ) -> Image_in_DB :
        # On prend une nouvelle ligne dans la table
        current_line = self.cursors[ self.current_cursor ].fetchone()
        
        # Si cette ligne est vide, c'est qu'on est au bout de la table, donc on
        # passe à la table suivante
        if current_line == None :
            self.current_cursor += 1
            
            # Si on a fait les 4 tables, on termine l'itération
            if self.current_cursor == 5 :
                raise StopIteration
            
            return self.__next__()
        
        return Image_in_DB (
                   current_line[0], # ID du compte Twitter
                   current_line[1], # ID du Tweet
                   current_line[ 4 : 4+CBIR_LIST_LENGHT ], # Features CBIR de l'image
                   self.current_cursor
               )
