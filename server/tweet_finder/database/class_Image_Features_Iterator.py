#!/usr/bin/python3
# coding: utf-8

try :
    from class_Image_in_DB import Image_in_DB
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .class_Image_in_DB import Image_in_DB


"""
Itérateur sur les images de Tweets contenues dans la base de données.

Cet objet doit uniquement être instancié par la méthode
"get_images_in_db_iterator()" de la classe "SQLite_or_MySQL" contenue dans le
fichier "class_SQLite_or_MySQL.py".
"""
class Image_Features_Iterator :
    def __init__( self, cursor ) :
        self.cursor = cursor
        
        # Ligne dans la base de données en cours de lecture
        self.current_line = self.cursor.fetchone()
        
        # Image de la ligne en cours de lecture (Car il peut y avoir 4 images
        # par ligne, pusique maximum de 4 images par Tweets)
        self.image_cursor = 0

    def __iter__( self ) :
        return self

    """
    @return Un objet Image_in_DB
    """
    def __next__( self ) -> Image_in_DB:
        if self.current_line == None :
            raise StopIteration
        
        # Si le curseur pointe vers une image non-vide
        if self.current_line[ 2 +  self.image_cursor ] != None :
            # A retourner
            # On doit le faire avant car on modifie des valeurs juste après
            to_return = Image_in_DB(
                self.current_line[0], # ID du compte Twitter
                self.current_line[1], # ID du Tweet
                [ float(value) for value in self.current_line[ 2 +  self.image_cursor ].split(';') ], # Features CBIR de l'image
                self.image_cursor + 1
            )
            
            # Si c'était la dernière image, on prépare pour passer au Tweet suivant
            if self.image_cursor == 3 :
                self.image_cursor = 0
                self.current_line = self.cursor.fetchone()
            
            # Sinon, on prépare pour passer à l'image suivante
            else :
                self.image_cursor += 1
                
            return to_return
        
        # Sinon, on passe au Tweet suivant
        self.image_cursor = 0
        self.current_line = self.cursor.fetchone()
        return self.__next__()
