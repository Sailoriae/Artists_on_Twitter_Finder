#!/usr/bin/python3
# coding: utf-8

"""
Ce script vérifie tous les ID de comptes enregistrés dans la base de données.
Si il y en a qui n'existent plus, tous leur Tweets sont supprimés, puis leur
enregistrement dans la base.
"""

import os
import sys
# On s'éxécute dans le répetoire "server"
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

import tweepy
import time

import parameters as param


"""
Connexion à l'API Twitter.
"""
auth = tweepy.OAuthHandler(param.API_KEY, param.API_SECRET)
auth.set_access_token(param.OAUTH_TOKEN, param.OAUTH_TOKEN_SECRET)
api = tweepy.API(auth)


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
Vérifie l'existence d'un compte Twitter.
@param account_id L'ID du compte Twitter à vérifier.
@return True si le compte existe (Même si il est privé, désactivé, ou suspendu).
        False si il est introuvable.
        None si on en sait rien.
"""
def check_account ( account_id : int ) -> bool :
    retry = True
    while retry :
        retry = False
        try :
            api.get_user( account_id )
            return True
        except tweepy.error.RateLimitError as error :
            print( "Limite atteinte en récupérant le nom du compte " + str(account_id) + "." )
            print( error.reason )
            print( "On va réessayer dans 60 secondes... ", end='' )
            time.sleep( 60 )
            print( "On réessaye !" )
            retry = True
        except tweepy.TweepError as error :
            print( "Erreur en récupérant le nom du compte " + str(account_id) + "." )
            print( error.reason )
            if error.api_code == 50 : # 50 = User not found
                return False
            return None

"""
Parcours de tous les ID de comptes dans la base.
"""
c = conn.cursor()
c.execute( "SELECT account_id FROM accounts" )
accounts_list = c.fetchall()

to_remove = []

for account_id in accounts_list :
    if check_account( account_id[0] ) == False :
        to_remove.append( account_id[0] )

if to_remove == [] :
    print( "Aucun compte à supprimer !" )
    sys.exit(0)

print( "Comptes à supprimer :", to_remove )
while True :
    answer = input( "Souhaitez-vous procéder ? [y/n] " )
    if answer == "y" :
        for account_id in to_remove :
            c = conn.cursor()
            
            print( "Suppression des Tweets du compte ID :", account_id )
            if param.USE_MYSQL_INSTEAD_OF_SQLITE :
                c.execute( "SELECT tweet_id FROM tweets WHERE account_id = %s", (account_id,) )
            else :
                c.execute( "SELECT tweet_id FROM tweets WHERE account_id = ?", (account_id,) )
            tweets_id = c.fetchall()
            
            if param.USE_MYSQL_INSTEAD_OF_SQLITE :
                for tweet_id in tweets_id :
                    print( "Suppression du Tweet :", tweet_id[0] )
                    c.execute( "DELETE FROM tweets WHERE tweet_id = %s", tweet_id )
                    c.execute( "DELETE FROM tweets_images_1 WHERE tweet_id = %s", tweet_id )
                    c.execute( "DELETE FROM tweets_images_2 WHERE tweet_id = %s", tweet_id )
                    c.execute( "DELETE FROM tweets_images_3 WHERE tweet_id = %s", tweet_id )
                    c.execute( "DELETE FROM tweets_images_4 WHERE tweet_id = %s", tweet_id )
            else :
                for tweet_id in tweets_id :
                    print( "Suppression du Tweet :", tweet_id[0] )
                    c.execute( "DELETE FROM tweets WHERE tweet_id = ?", tweet_id )
                    c.execute( "DELETE FROM tweets_images_1 WHERE tweet_id = ?", tweet_id )
                    c.execute( "DELETE FROM tweets_images_2 WHERE tweet_id = ?", tweet_id )
                    c.execute( "DELETE FROM tweets_images_3 WHERE tweet_id = ?", tweet_id )
                    c.execute( "DELETE FROM tweets_images_4 WHERE tweet_id = ?", tweet_id )
            
            print( "Suppression du compte ID :", account_id )
            if param.USE_MYSQL_INSTEAD_OF_SQLITE :
                c.execute( "DELETE FROM accounts WHERE account_id = %s", (account_id,) )
            else :
                c.execute( "DELETE FROM accounts WHERE account_id = ?", (account_id,) )
            
            conn.commit()
        
        break
    
    elif answer == "n" :
        sys.exit(0)
