#!/usr/bin/python3
# coding: utf-8

"""
Ce script vérifie tous les ID de comptes enregistrés dans la base de données.
Si il y en a qui n'existent plus, tous leur Tweets sont supprimés, puis leur
enregistrement dans la base.
Attention : Ce script supprime aussi les comptes suspendus.
Sinon il vaut vérifier l'existence des compte un par uns, et c'est trop long.
Ce script ne supprime pas les comptes qui ont étés passés en privés.
Et aucune idée des comptes désactivés.
API utilisée : "GET users/lookup", documentation :
https://developer.twitter.com/en/docs/twitter-api/v1/accounts-and-users/follow-search-get-users/api-reference/get-users-lookup
"""

import tweepy

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

# On s'éxécute dans le répetoire "server", et l'ajouter au PATH
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

import parameters as param


"""
Connexion à l'API Twitter.
"""
auth = tweepy.OAuthHandler(param.API_KEY, param.API_SECRET)
auth.set_access_token(param.OAUTH_TOKEN, param.OAUTH_TOKEN_SECRET)

# Tweepy gère l'attente lors d'une rate limit !
api = tweepy.API( auth, 
                  wait_on_rate_limit = True,
                  wait_on_rate_limit_notify  = True )


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
Listage des ID de comptes Twitter enregistrés dans la base de données.
"""
c = conn.cursor()
c.execute( "SELECT account_id FROM accounts" )
accounts_list = c.fetchall()

accounts_in_db = []
for account_id in accounts_list :
    accounts_in_db.append( account_id[0] )

print( "Il y a", len(accounts_in_db), "comptes Twitter dans la base de données." )


"""
Listage des ID de comptes Twitter qui existent encore.
"""
print( "Listage des ID de comptes Twitter qui existent encore." )

cursor = 0 # Curseur de parcours de la liste accounts_in_db

accounts_on_twitter = []
while True :
    hundred_accounts = accounts_in_db[ cursor : cursor + 100 ]
    if hundred_accounts == [] : # On est arrivés au bout
        print( "Fin du listage des ID de comptes Twitter qui existent encore." )
        break
    
    for account in api.lookup_users( user_ids = hundred_accounts ) :
        accounts_on_twitter.append( account.id )
    
    print( "Comptes analysés :", cursor, "/", str(len(accounts_in_db)) + ", valides :", len(accounts_on_twitter) )
    cursor += 100


"""
Comparaison de la liste des ID de comptes Twitter enregistrés dans la base de
données, avec la liste des ID de comptes Twitter qui existent encore.
"""
to_remove = []

for account_id in accounts_in_db :
    if not account_id in accounts_on_twitter :
        to_remove.append( account_id )


"""
Suppression des comptes trouvés comme à supprimer.
"""
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
