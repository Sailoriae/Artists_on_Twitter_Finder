#!/usr/bin/python3
# coding: utf-8

"""
Ce script permet de vérifier qu'il n'y ait pas de retweet stocké dans la BDD.
Note : Les retweets ont un ID différent du Tweet d'origine. Si un retweet a été
stocké, on peut essayer de le détecter en utilisant une API connue et bien
documentée pour être certain qu'on détecte les retweets (Car AOTF utilise
plusieurs API différentes, donc des privées via SNScrape).
"""

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
from tweet_finder.twitter.class_TweepyAbstraction import TweepyAbstraction

# Connexion à l'API Twitter
twitter = TweepyAbstraction( param.API_KEY, param.API_SECRET,
                             param.OAUTH_TOKEN, param.OAUTH_TOKEN_SECRET )

# Vérifier rapidement qu'on détecte bien les retweets
# Sinon, il faut corriger le script (Et peut-être le serveur AOTF)
tweet = twitter.get_multiple_tweets( [ 1526957996747722753 ] )[0]
if not "retweeted_status" in tweet._json :
    raise Exception( "Impossible de détecter un vrai retweet" )

# Connexion à la base de données
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

# Obtenir tous les ID de Tweets dans la BDD par ordre décroissant
# On est obligés de les obtenir d'un coup, sinon on risque de crasher
c = conn.cursor()
c.execute( "SELECT tweet_id FROM tweets ORDER BY tweet_id DESC" )
tweets = c.fetchall()
tweets = [ tweet[0] for tweet in tweets ]

# Itération sur tous les Tweets
cursor = 0
count_retweets = 0
while True :
    hundred_tweets = tweets[ cursor : cursor + 100 ]
    if len( hundred_tweets ) == 0 : break
    cursor += len( hundred_tweets )
    
    # On utilise l'API v1 qu'on connait bien
    for tweet in twitter.get_multiple_tweets( hundred_tweets ) :
        if "retweeted_status" in tweet._json :
            count_retweets += 1
            if tweet._json["full_text"][:4] != "RT @" :
                print( f"Le Tweet ID {tweet.id} semble être un retweet, mais n'y ressemble pas" )
            print( f"Le Tweet ID {tweet.id} semble être un retweet" )
    
    print( f"{cursor} Tweets obtenus, {count_retweets} retweets détectés" )
