#!/usr/bin/python3
# coding: utf-8

"""
Ce script permet de supprimer les Tweets (Et ainsi les empreintes de leurs
images) dont l'ID du compte Twitter associé n'est pas stocké dans la BDD.

En gros, il nettoie la base de données des enregistrement en trop.
LE SERVEUR DOIT ETRE ETEINT !
"""

import sys

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
On demande à l'utilisateur si le serveur est bien éteint.
"""
while True :
    answer = input( "Le serveur est-il bien éteint ? [y/n] " )
    if answer == "y" :
        break
    elif answer == "n" :
        print( "Veuillez d'abord éteindre le serveur avant d'exécuter ce script !" )
        sys.exit(0)


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
Listage des ID des Tweets qui n'ont pas d'enregistrement dans la table des
comptes Twitter.
"""
print( "Vérification des enregistrements dans la table des Tweets..." )

c = conn.cursor()
c.execute( """SELECT tweet_id
              FROM tweets
              WHERE NOT EXISTS (
                  SELECT *
                  FROM accounts
                  WHERE accounts.account_id = tweets.account_id
              )""" )
tweets_id = c.fetchall()


"""
On demande à l'utilisateur si il souhaite continuer.
"""
if len(tweets_id) > 0 :
    while True :
        answer = input( f"{len(tweets_id)} Tweets à supprimer, souhaitez-vous continuer ? [y/n] " )
        if answer == "y" :
            break
        elif answer == "n" :
            print( "Aucun Tweet n'a été supprimé !" )
            sys.exit(0)
else :
    print( "Aucun Tweet à supprimer !" )
    sys.exit(0)

"""
Effacer les Tweets à supprimer.
"""
for tweet_id in tweets_id :
    print( f"Suppression du Tweet ID {tweet_id[0]}..." )
    
    if param.USE_MYSQL_INSTEAD_OF_SQLITE :
        c.execute( "DELETE FROM tweets WHERE tweet_id = %s", tweet_id )
    
    else :
        c.execute( "DELETE FROM tweets WHERE tweet_id = ?", tweet_id )
    
    conn.commit()

print( "Terminé !" )
