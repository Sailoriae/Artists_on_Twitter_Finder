#!/usr/bin/python3
# coding: utf-8

"""
Ce script permet d'obtenir les clés "oauth_token" et "oauth_token_secret" pour
une application Twitter, c'est à dire l'accès à l'API publique de Twitter.
Rappel : Une application est un couple de clés "api_key" et "api_secret".

ATTENTION : Script à exécuter sur un ordinateur de bureau, et non un serveur,
car il ouvre le navigateur web !
"""

import webbrowser
import tweepy

consumer_key = input( "Veuillez entrer votre \"api_key\" : " ).strip()
consumer_secret = input( "Veuillez entrer votre \"api_secret\" : " ).strip()
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

webbrowser.open(auth.get_authorization_url())

pin = input( "Veuillez entrer le code PIN affiché par Twitter : " ).strip()

token = auth.get_access_token( verifier = pin )

print( "Tokens d'accès à ce compte Twitter :" )
print( " - \"oauth_token\" : " + token[0] )
print( " - \"oauth_token_secret\" : " + token[1] )
