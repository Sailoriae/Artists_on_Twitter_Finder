#!/usr/bin/python3
# coding: utf-8

"""
Ce script m'a permis d'ajouter les noms des images à ma base de données, afin
de ne pas avoir à la réinitialiser. Je l'ai sauvegardé dans le GIT, car
il peut peut-être réutilisé.
L'utilisation de la fonction "statuses_lookup()" de Tweepy, permettant de
recevoir plusieurs Tweets (Jusqu'à 100) en une seule requête, est très
intéressante.
Ainsi, il peut scanner en moyenne 600 000 Tweets en 1h40.
"""

# Deuxième passe, plus précise
SECOND_PASS = True

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
INSERER LE NOM DE CHAQUE IMAGE DE TOUS LES TWEETS DE LA BASE.
"""
c = conn.cursor( buffered = True )
if not SECOND_PASS :
    c.execute( "SELECT tweet_id FROM tweets" )
else :
    c.execute( """SELECT DISTINCT * FROM
                  (
                      ( SELECT tweet_id AS a FROM tweets_images_1 WHERE image_name IS NULL )
                      UNION
                      ( SELECT tweet_id AS b FROM tweets_images_2 WHERE image_name IS NULL )
                      UNION
                      ( SELECT tweet_id AS c FROM tweets_images_3 WHERE image_name IS NULL )
                      UNION
                      ( SELECT tweet_id AS d FROM tweets_images_4 WHERE image_name IS NULL )
                  ) AS e""" )

count = 0
last_one = False
while True :
    hundred_tweets = []
    
    while True :
        fetchone = c.fetchone()
        if fetchone == None :
            last_one = True
            break
        hundred_tweets.append( fetchone[0] )
        if len( hundred_tweets ) >= 100 :
            break
    
    count += len( hundred_tweets )
    tweets = api.statuses_lookup( hundred_tweets, trim_user = True, tweet_mode = 'extended' )
    
    local_c = conn.cursor()
    
    for tweet in tweets :
        tweet_images_url = []
        
        try :
            for tweet_media in tweet._json["extended_entities"]["media"] :
                if tweet_media["type"] == "photo" :
                    tweet_images_url.append( tweet_media["media_url_https"] )
        except KeyError as error:
            print( tweet.id, "n'a pas de médias." )
            print(error)
            continue
        
        if len( tweet_images_url ) == 0 :
            print( tweet.id, "n'a pas de médias trouvé." )
            continue
        
        if len( tweet_images_url ) >= 1 :
            local_c.execute( "UPDATE tweets_images_1 SET image_name = %s WHERE tweet_id = %s",
                             ( tweet_images_url[0].replace("https://pbs.twimg.com/media/", ""), tweet.id ) )
        if len( tweet_images_url ) >= 2 :
            local_c.execute( "UPDATE tweets_images_2 SET image_name = %s WHERE tweet_id = %s",
                             ( tweet_images_url[1].replace("https://pbs.twimg.com/media/", ""), tweet.id ) )
        if len( tweet_images_url ) >= 3 :
            local_c.execute( "UPDATE tweets_images_3 SET image_name = %s WHERE tweet_id = %s",
                             ( tweet_images_url[2].replace("https://pbs.twimg.com/media/", ""), tweet.id ) )
        if len( tweet_images_url ) >= 4 :
            local_c.execute( "UPDATE tweets_images_4 SET image_name = %s WHERE tweet_id = %s",
                             ( tweet_images_url[3].replace("https://pbs.twimg.com/media/", ""), tweet.id ) )
    
    conn.commit()
    print( "Tweets analysés :", count )
    
    if last_one :
        print( "Fin de traitement !" )
        break
