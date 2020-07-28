#!/usr/bin/python3
# coding: utf-8

"""
Ce script permet d'extraire la liste des ID des Tweets qui ont eu un problème
de traitement, et de retenter de les indexer.
"""

import os
import sys
# On s'éxécute dans le répetoire "server", et l'ajouter au PATH
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

import re
from tweet_finder import CBIR_Engine_with_Database


"""
Lecture du fichier "class_CBIR_Engine_with_Database_errors.log".
"""

try :
    f = open( "class_CBIR_Engine_with_Database_errors.log", "r" )
except FileNotFoundError :
    print( "Fichier \"class_CBIR_Engine_with_Database_errors.log\" inexistant !" )
    sys.exit(0)

lines = f.readlines()
f.close()

regex_expr = re.compile( r"Erreur avec le Tweet : ([0-9]+) !" )
founded_ids = []

for l in lines :
    result = re.search( regex_expr, l )
    if result != None :
        founded_ids.append( int( result.group( 1 ) ) )

print( "Tweets trouvés :", founded_ids )


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
Tentative d'indexation des Tweets trouvés !
"""
engine = CBIR_Engine_with_Database( DEBUG = True )
for tweet_id in founded_ids :
    engine.index_tweet( tweet_id, FORCE_INDEX = True )
