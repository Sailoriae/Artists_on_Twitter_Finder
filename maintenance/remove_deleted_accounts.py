#!/usr/bin/python3
# coding: utf-8

"""
Ce script vérifie tous les ID de comptes enregistrés dans la base de données.
Si il y en a qui n'existent plus, tous leur Tweets sont supprimés, puis leur
enregistrement dans la base.

Attention : Ce script supprime les comptes : Supprimés, suspendus, ou sur la
liste noire d'AOTF. Ce script ne supprime pas les comptes : Passés en privé.
Et aucune idée de ce qu'il fait des comptes désactivés.

API utilisée : "GET users/lookup", documentation :
https://developer.twitter.com/en/docs/twitter-api/v1/accounts-and-users/follow-search-get-users/api-reference/get-users-lookup
"""

import sys
import tweepy

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
from tweet_finder.blacklist import BLACKLIST


"""
Connexion à l'API Twitter.
"""
auth = tweepy.OAuthHandler(param.API_KEY, param.API_SECRET)
auth.set_access_token(param.OAUTH_TOKEN, param.OAUTH_TOKEN_SECRET)

# Tweepy gère l'attente lors d'une rate limit !
api = tweepy.API( auth,
                  wait_on_rate_limit = True )


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

print( f"Il y a {len(accounts_in_db)} comptes Twitter dans la base de données." )


"""
Listage des ID de comptes Twitter qui existent encore.
"""
print( "Listage des ID de comptes Twitter qui existent encore." )

cursor = 0 # Curseur de parcours de la liste accounts_in_db

accounts_on_twitter = []
blacklisted = [] # Pour faire un "print()" à la fin
while True :
    hundred_accounts = accounts_in_db[ cursor : cursor + 100 ]
    if hundred_accounts == [] : # On est arrivés au bout
        print( "Fin du listage des ID de comptes Twitter qui existent encore." )
        break
    
    try :
        for account in api.lookup_users( user_id = hundred_accounts ) :
            if int( account.id ) in BLACKLIST :
                blacklisted.append( ( account.screen_name, account.id ) )
            else :
                accounts_on_twitter.append( account.id )
    except tweepy.errors.NotFound as error :
        if 17 in error.api_codes : # No user matches for specified terms
            print( "C'est étrange que 100 comptes d'un bloc ne soient plus valides !" )
            pass
        else :
            raise error
    
    print( f"Comptes analysés : {cursor}/{str(len(accounts_in_db))}, valides : {len(accounts_on_twitter)}" )
    cursor += 100

for account_name, account_id in blacklisted :
    print( f"Le compte @{account_name} (ID {account_id}) est sur la liste noire d'AOTF. Son indexation sera supprimée !" )


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

print( f"Comptes à supprimer : {', '.join( [ str(account_id) for account_id in to_remove ] )}" )
while True :
    answer = input( "Souhaitez-vous procéder ? [y/n] " )
    if answer == "y" :
        for account_id in to_remove :
            c = conn.cursor()
            
            print( f"Suppression des Tweets du compte ID {account_id}..." )
            if param.USE_MYSQL_INSTEAD_OF_SQLITE :
                c.execute( "DELETE FROM tweets WHERE account_id = %s", (account_id,) )
            else :
                c.execute( "DELETE FROM tweets WHERE account_id = ?", (account_id,) )
            
            print( f"Suppression du compte ID {account_id}..." )
            if param.USE_MYSQL_INSTEAD_OF_SQLITE :
                c.execute( "DELETE FROM accounts WHERE account_id = %s", (account_id,) )
            else :
                c.execute( "DELETE FROM accounts WHERE account_id = ?", (account_id,) )
            
            conn.commit()
        
        print( "Terminé !" )
        break
    
    elif answer == "n" :
        print( "Aucun compte n'a été supprimé !" )
        sys.exit(0)
