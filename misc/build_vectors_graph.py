#!/usr/bin/python3
# coding: utf-8


import sys
print( "Ne pas exécuter ce script sans savoir ce qu'il fait." )
sys.exit(0)


"""
Ce script permet de construire le graphe des images = vecteurs stockés dans
la base de données.
"""

from time import time
from statistics import mean

# On travaille dans le répertoire racine du serveur AOTF
# On bouge dedans, et on l'ajoute au PATH
from os.path import abspath as get_abspath
from os.path import dirname as get_dirname
from os import chdir as change_wdir
from os import getcwd as get_wdir
from sys import path
change_wdir(get_dirname(get_abspath(__file__)))
change_wdir( "../server" )
path.append(get_wdir())

import parameters as param
#from tweet_finder.database.class_Graph_Search import Graph_Search
from class_Graph_Search import Graph_Search # Ce fichier était destiné à être dans le répertoire "database"

CBIR_LIST_LENGHT = 240


"""
Connexion séparée à la base de données (Pour ne pas avoir à faire un curseur
avec mémoire cache = curseur buffered).
"""
if param.USE_MYSQL_INSTEAD_OF_SQLITE :
    import mysql.connector
    conn = mysql.connector.connect(
               host = param.MYSQL_ADDRESS,
               port = param.MYSQL_PORT,
               user = param.MYSQL_USERNAME,
               password = param.MYSQL_PASSWORD,
               database = param.MYSQL_DATABASE_NAME
           )
else :
    import sqlite3
    conn = sqlite3.connect(
               param.SQLITE_DATABASE_NAME,
           )


"""
Initialisation du moteur de recherche.
"""
engine = Graph_Search()


"""
Pour chacune des 4 tables d'images, on liste tous les vecteurs présent, et on
les ajoute au graphe.
"""
c = conn.cursor()
for table_id in [4, 3, 2, 1] :
    c.execute( f"SELECT * FROM tweets_images_{table_id}" )
    
    count = 0
    times = []
    while True :
        current_image = c.fetchone()
        if current_image == None :
            break
        
        image_id = current_image[1]
        vector = current_image[ 2 : 2+CBIR_LIST_LENGHT ]
        
        # ATTENTION : ON NE PEUT PAS AJOUTER DANS LE GRAPHE LES IMAGES DONT
        # LEUR VECTEUR EST UNE LISTE DE NULL
        if vector[0] != None :
            start = time()
            engine.add_node( image_id, table_id, vector )
            times.append( time() - start )
        
        count += 1
        if count%10 == 0 : # On print() toutes les 10 images
            print( f"tweets_images_{table_id} : {count} images traitées, en moyenne {mean(times)} secondes par image")
        
