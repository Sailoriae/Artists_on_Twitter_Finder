#!/usr/bin/python3
# coding: utf-8

import sys
print( "Ce script n'est plus utile car le réessai de Tweets est désormais intégré au serveur." )
sys.exit(0)


"""
Ce script permet d'extraire la liste des ID des Tweets qui ont eu un problème
de traitement, et de retenter de les indexer.
"""

import os
import sys

# On s'éxécute dans le répertoire "server"
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

import parameters as param
from tweet_finder import Tweets_Indexer
from tweet_finder.analyse_tweet_json import analyse_tweet_json
from tweet_finder.twitter import TweepyAbstraction

import re
from queue import Queue


"""
Lecture du fichier "class_CBIR_Engine_for_Tweets_Images_errors.log".
"""

try :
    f = open( "class_CBIR_Engine_for_Tweets_Images_errors.log", "r" )
except FileNotFoundError :
    print( "Fichier \"class_CBIR_Engine_for_Tweets_Images_errors.log\" inexistant !" )
    sys.exit(0)

lines = f.readlines()
f.close()

regex_expr = re.compile( r"Erreur avec le Tweet : ([0-9]+) !" )
found_ids = []

for l in lines :
    result = re.search( regex_expr, l )
    if result != None :
        found_ids.append( int( result.group( 1 ) ) )

print( "Tweets trouvés :", found_ids )


"""
Même problème de SSL que dans "app.py".
"""
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


"""
Connexion à l'API Twitter.
"""
twitter = TweepyAbstraction( param.API_KEY,
                             param.API_SECRET,
                             param.OAUTH_TOKEN,
                             param.OAUTH_TOKEN_SECRET )

"""
Tentative d'indexation des Tweets trouvés !
"""
tweets_queue = Queue()
for tweet_id in found_ids :
    tweet = twitter.get_tweet( tweet_id )
    if tweet != None :
        tweets_queue.put( analyse_tweet_json( tweet._json ) )
tweets_queue.put( None ) # Cloturer la file

engine = Tweets_Indexer( DEBUG = True )
engine.index_tweets( "", tweets_queue, FORCE_INDEX = True )
