#!/usr/bin/python3
# coding: utf-8

"""
Ce script permet d'analyser les premiers Tweets trouvés de chaque résultat
du serveur AOTF. Il nécesite le fichier "results.log", et donc que le
paramètre "ENABLE_LOGGING" soit activé.
"""

import json
file = open( "../server/results.log", "r" )
lines = file.readlines()
file.close()
dicts = []
for l in lines :
    dicts.append(json.loads(l))

first_results = {} # Distance -> Liste d'URL d'entrée
count_matches = {} # Distance -> Compteur

for d in dicts :
    if len( d["results"] ) == 0:
        continue
    first_match_distance = d["results"][0]["distance"]
    if first_match_distance in first_results :
        if d["input"] in first_results[first_match_distance] :
            continue # On sort des doublons
        first_results[first_match_distance].append( d["input"] )
        count_matches[first_match_distance] += 1
    else :
        first_results[first_match_distance] = [ d["input"] ]
        count_matches[first_match_distance] = 1

print( "Premiers résultats classés par distance :" )
for distance, inputs in sorted( first_results.items() ) :
    for url in inputs :
        print( f"{distance} {url}" )

print( "Compteurs de premiers résultats :" )
for distance, compteur in sorted( count_matches.items() ) :
    print( f" - {compteur} avec une distance de {distance}" )
