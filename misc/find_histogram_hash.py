#!/usr/bin/python3
# coding: utf-8

"""
Ce script sert à chercher une méthode de "hash" des histogrammes, afin de
sortir une valeur unique pour chaque histogramme.

LE BUT : Pré-filtrer dans la BDD avec une requête SQL pour que moins d'images
soient comparées.
Il faudrait pousser ça plus loin afin de faire le maximum de filtrages dans
la BDD !
"""

import os
import numpy as np
import statistics as stats

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


"""
Connexion à la base de données.
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
Tester la méthode de hash.
"""
# Fonctions de la méthode de "hash"
# J'en ai testé plusieurs, et faire la somme semble être la plus efficace
# Le but est d'avoir un écart-type proche de celui d'une loi uniforme sur le même intervalle
# Après quelques tests, un bon ecart pour le WHERE serait +/- 0.3
def method( features_list ) :
    return sum( features_list )

c = conn.cursor()
c.execute( "SELECT * FROM tweets_images_1 LIMIT 10000" )

values = []
for tweet in c.fetchall() :
    if tweet[2] == None :
        continue
    values.append( method( tweet[2:] ) )

print( "TEST AVEC LES IMAGES DE LA BASE DE DONNEES :" )
print( " - Nombre de valeurs :", len( values ) )
print( " - Minimum :", min( values ) )
print( " - Maximum :", max( values ) )
print( " - Moyenne :", stats.mean( values ) )
print( " - Médiane :", stats.median( values ) )
print( " - Ecart-type :", stats.pstdev( values ) )
print( " - Variance :", stats.variance( values ) )

# Génération sur le même intervalle d'une loi uniforme
compare_values = np.random.uniform( low = min(values), high = max(values), size = (10000,) )

print( "COMPARAISON AVEC UNE LOI UNIFORME SUR LE MEME INTERVALLE :" )
print( " - Moyenne :", stats.mean( compare_values ) )
print( " - Médiane :", stats.median( compare_values ) )
print( " - Ecart-type :", stats.pstdev( compare_values ) )
print( " - Variance :", stats.variance( compare_values ) )

print( "INDICE DE COMPARAISON :", stats.pstdev( compare_values ) / stats.pstdev( values ) )
print( "Plus il est proche de 1, mieux c'est." )
