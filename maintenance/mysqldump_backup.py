#!/usr/bin/python3
# coding: utf-8

"""
Ce script permet de sauvegarder la base de données en faisant un Dump MySQL.
Au passage, il supprime les anciennes sauvegardes qui ont plus de 6 semaines.
La raison de ce script est qu'il va chercher tout seul les paramètres dans
le fichier "parameters.py".
"""

import os
import sys
from datetime import datetime

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


if sys.platform not in [ "linux", "linux2" ] :
    print( "Ce script ne peut être exécuté que sur un système Linux." )
    sys.exit(0)

if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
    print( "Le paramètre \"USE_MYSQL_INSTEAD_OF_SQLITE\" est sur \"False\"." )
    sys.exit(0)

if os.path.isfile( "../backups/AOTF_" + datetime.today().strftime("%Y-%m-%d") + ".sql" ) :
    print( "Une sauvegarde de la base de données a déjà été exécutée aujourd'hui." )
    sys.exit(0)

print( "Sauvegarde de la base de données d'Artists on Twitter Finder..." )
os.system( "mkdir -p ../backups" )
os.environ["MYSQL_PWD"] = param.MYSQL_PASSWORD # Ne pas exposer le MDP dans la commande du processus
os.system( f"mysqldump -h {param.MYSQL_ADDRESS} -P {param.MYSQL_PORT} -u {param.MYSQL_USERNAME} --hex-blob --single-transaction --no-tablespaces Artists_on_Twitter_Finder accounts tweets reindex_tweets > ../backups/AOTF_$(date '+%Y-%m-%d').sql" )
os.system( "find ../backups -name \"*.sql\" -mtime +42 -exec rm {} \;" )
print( "Sauvegarde terminée !" )
