#!/usr/bin/python3
# coding: utf-8

"""
Ce script permet de supprimer les Tweets dont l'ID du compte Twitter associé
n'est pas stocké dans la BDD, puis supprime les images de ces Tweets.
Puis, il va vérifier qu'il n'y ait pas d'images de Tweet sans Tweet enregistré.

En gros, il nettoie la base de données des enregistrement en trop.
LE SERVEUR DOIT ETRE ETEINT !
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

# On s'éxécute dans le répetoire "server", et l'ajouter au PATH
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

import parameters as param


"""
On demande à l'utilisateur si le serveur est bien éteint.
"""
while True :
    answer = input( "Le serveur est-il bien éteint ? [y/n] " )
    if answer == "y" :
        break
    elif answer == "n" :
        print( "Veuillez d'abord éteindre le serveur avant d'éxécuter ce script !" )
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
print( " => Nom réel de la table : tweets" )

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
count = str(len(tweets_id))
# Sinon, on le laisse continuer pour aller à la vérification de l'intégrité
if len(tweets_id) > 0 :
    while True :
        answer = input( count + " Tweets à supprimer, souhaitez-vous continuer ? [y/n] " )
        if answer == "y" :
            break
        elif answer == "n" :
            print( "Aucun Tweet n'a été supprimé !" )
            sys.exit(0)
else :
    print( "Aucun Tweet à supprimer !" )

"""
Effacer les Tweets à supprimer.
"""
for tweet_id in tweets_id :
    print( "Suppression du Tweet :", tweet_id[0] )
    
    if param.USE_MYSQL_INSTEAD_OF_SQLITE :
        c.execute( "DELETE FROM tweets_images_1 WHERE tweet_id = %s", tweet_id )
        c.execute( "DELETE FROM tweets_images_2 WHERE tweet_id = %s", tweet_id )
        c.execute( "DELETE FROM tweets_images_3 WHERE tweet_id = %s", tweet_id )
        c.execute( "DELETE FROM tweets_images_4 WHERE tweet_id = %s", tweet_id )
        c.execute( "DELETE FROM tweets WHERE tweet_id = %s", tweet_id )
    
    else :
        c.execute( "DELETE FROM tweets_images_1 WHERE tweet_id = ?", tweet_id )
        c.execute( "DELETE FROM tweets_images_2 WHERE tweet_id = ?", tweet_id )
        c.execute( "DELETE FROM tweets_images_3 WHERE tweet_id = ?", tweet_id )
        c.execute( "DELETE FROM tweets_images_4 WHERE tweet_id = ?", tweet_id )
        c.execute( "DELETE FROM tweets WHERE tweet_id = ?", tweet_id )
    
    conn.commit()


"""
Vérification de l'intégrité des tables d'images de Tweets.
C'est à dire qu'on vérifie qu'il n'y ait pas d'images de Tweet sans
Tweet enregistré.
"""
while True :
    answer = input( "Souhaitez-vous aussi vérifier l'intégrité des tables d'images de Tweets ? [y/n] " )
    if answer == "y" :
        break
    elif answer == "n" :
        sys.exit(0)

for image_id in ["1", "2", "3", "4"] :
    print( "Vérification des enregistrements dans la table des images numéro " + image_id + " de Tweets..." )
    print( " => Nom réel de la table : tweets_images_" + image_id )
    
    c = conn.cursor()
    c.execute( """SELECT tweet_id
                  FROM tweets_images_""" + image_id + """
                  WHERE NOT EXISTS (
                      SELECT *
                      FROM tweets WHERE tweets.tweet_id = tweets_images_""" + image_id + """.tweet_id
                  )""" )
    tweets_id = c.fetchall()
    
    if len(tweets_id) > 0 :
        while True :
            answer = input( count + " images numéro " + image_id + " de Tweets à supprimer, souhaitez-vous continuer ? [y/n] " )
            if answer == "y" :
                break
            elif answer == "n" :
                print( "Aucune image de Tweet n'a été supprimée !" )
                sys.exit(0)
    else :
        print( "Aucune image de Tweet à supprimer !" )
    
    for tweet_id in tweets_id :
        print( "Suppression de l'image numéro " + image_id + " du Tweet :", tweet_id[0] )
        
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            c.execute( "DELETE FROM tweets_images_" + image_id + " WHERE tweet_id = %s", tweet_id )
        
        else :
            c.execute( "DELETE FROM tweets_images_" + image_id + " WHERE tweet_id = ?", tweet_id )
        
        conn.commit()
