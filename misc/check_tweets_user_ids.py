#!/usr/bin/python3
# coding: utf-8

"""
Ce script m'a permis de vérifier les ID des comptes associés aux Tweets dans ma
base de données, afin de ne pas avoir à la réinitialiser. Je l'ai sauvegardé
dans le GIT, car il peut peut-être réutilisé.
J'ai été obligé de faire cette opération car il y avait un problème avec
SNScrape qui n'enregistrait pas l'ID du compte présent dans le JSON du Tweet.
Ce problème a été corrigé.
L'utilisation de la fonction "statuses_lookup()" de Tweepy, permettant de
recevoir plusieurs Tweets (Jusqu'à 100) en une seule requête, est très
intéressante.
"""


import sys
print( "Ne pas exécuter ce script sans savoir ce qu'il fait." )
sys.exit(0)


"""
CONNEXION API TWITTER.
"""
API_KEY = ""
API_SECRET = ""
OAUTH_TOKEN = ""
OAUTH_TOKEN_SECRET = ""

import tweepy

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

# Tweepy gère l'attente lors d'une rate limit !
api = tweepy.API( auth, 
                  wait_on_rate_limit = True,
                  wait_on_rate_limit_notify  = True )


"""
CONNEXION A LA BASE DE DONNEES.
"""
MYSQL_ADDRESS = "localhost"
MYSQL_PORT = 3306
MYSQL_USERNAME = ""
MYSQL_PASSWORD = ""
MYSQL_DATABASE_NAME = ""

import mysql.connector

conn = mysql.connector.connect( host = MYSQL_ADDRESS,
                                port = MYSQL_PORT,
                                user = MYSQL_USERNAME,
                                password = MYSQL_PASSWORD,
                                database = MYSQL_DATABASE_NAME )


"""
VERIFIER L'ID DE COMPTE ASSOCIE A TOUS LES TWEETS DE LA BASE.
"""
from time import sleep

c = conn.cursor( buffered = True )
c.execute( "SELECT tweet_id, account_id FROM tweets" )

count = 0
count_modified = 0
last_one = False
while True :
    hundred_tweets = []
    hundred_tweets_dict = {}
    
    while True :
        fetchone = c.fetchone()
        if fetchone == None :
            last_one = True
            break
        hundred_tweets.append( fetchone[0] )
        hundred_tweets_dict[ str(fetchone[0]) ] = str(fetchone[1])
        if len( hundred_tweets ) >= 100 :
            break
    
    count += len( hundred_tweets )
    
    tweets = [] # Reset au cas où
    while True :
        try :
            tweets = api.statuses_lookup( hundred_tweets, trim_user = True, tweet_mode = 'extended' )
        except tweepy.error.TweepError as error :
            print( error )
            sleep( 30 )
        else :
            break
    
    local_c = conn.cursor()
    
    for tweet in tweets :
#        user_id = tweet._json["user_id_str"] # API v2
        user_id = tweet._json["user"]["id"] # API v1.1
        tweet_id = tweet._json["id_str"]
        if str(user_id) != hundred_tweets_dict[ tweet_id ] :
            local_c.execute( "UPDATE tweets SET account_id = %s WHERE tweet_id = %s",
                             ( user_id, tweet_id ) )
            count_modified += 1
    
    conn.commit()
    print( "Tweets analysés :", count, "- Dont Tweets modifiés :", count_modified )
    
    if last_one :
        print( "Fin de traitement !" )
        break
