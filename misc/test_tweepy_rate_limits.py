#!/usr/bin/python3
# coding: utf-8

import sys
print( "Ne pas exécuter ce script sans savoir ce qu'il fait." )
sys.exit(0)

"""
Ce script va tester si Tweepy est limité par adresse IP ou par clés
d'authentification.
Il émet beaucoup de requêtes. Lorsqu'une limite est atteinte, redémarrez le
script avec d'autres clés d'authentification.
Si il re-fonctionne directement, c'est que les rate limits ne sont pas par
adresse IP.
"""

print( "Veuillez entrer les clés suivantes..." )
api_key = input( "\"api_key\" : " )
api_secret = input( "\"api_secret\" : " )
oauth_token = input( "\"oauth_token\" : " )
oauth_token_secret = input( "\"oauth_token_secret\" : " )
print( "On va envoyer pleins de requêtes pour atteindre la \"rate limit\"." )
print( "Une fois atteinte, veuillez tuer ce script et le redémarrer avec d'autres clés d'authentification.")

import tweepy

auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(oauth_token, oauth_token_secret)
api = tweepy.API( auth, wait_on_rate_limit = True, wait_on_rate_limit_notify  = True  )

while True :
    for tweet in tweepy.Cursor( api.user_timeline, screen_name = "jack" ).items() :
        pass
