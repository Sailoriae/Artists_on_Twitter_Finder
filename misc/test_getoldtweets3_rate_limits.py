#!/usr/bin/python3
# coding: utf-8

"""
Ce script va tester si GOT3 est limité par adresse IP ou par token
d'authentification.
Il émet beaucoup de requêtes. Lorsqu'une limite est atteinte, redémarrez le
script avec un autre token.
Si il re-fonctionne directement, c'est que les rate limits ne sont pas par
adresse IP.

Réponse au 12 aout 2020 : GOT3 est limité sur le token d'authentification, mais
pas sur l'adresse IP.
Bon, peut-être aussi sur l'adresse IP, mais ça serait bien plus loin !
"""

auth_token = input( "Veuillez entrer un \"auth_token\" : " )
print( "On va envoyer pleins de requêtes pour atteindre la \"rate limit\"." )
print( "Une fois atteinte, veuillez tuer ce script et le redémarrer avec un autre \"auth_token\".")

import os
import sys
sys.path.append(os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"), "tweet_finder"))

from lib_GetOldTweets3 import manager as GetOldTweets3_manager

tweetCriteria = GetOldTweets3_manager.TweetCriteria().setQuerySearch( "from:jack" )

while True :
    GetOldTweets3_manager.TweetManager.getTweets( tweetCriteria,
                                                  auth_token = auth_token )
