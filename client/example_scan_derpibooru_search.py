#!/usr/bin/python3
# coding: utf-8

import requests

from class_AOTF_Client import AOTF_Client


"""
Fonction permettant de populer la base de données autour d'une recherche sur
Derpibooru.
@param SEARCH_TO_SCAN Recherche sur Derpibooru à scanner. 
@param LIMIT Limite du nombre de posts Derpibooru à envoyer.

Note : Les images sont envoyées dans l'ordre du score, en descendant. De plus,
aucun filtre n'est appliqué !
"""
def scan_derpibooru_search ( SEARCH_TO_SCAN, LIMIT = None ) :
    server = AOTF_Client()
    
    # Liste des artistes déjà envoyé, ça ne sert à rien de faire une autre
    # requête au serveur pour cet artiste, puisqu'on veut juste populer sa
    # base de données
    launched_artists = []
    
    page_number = 1
    count = 0
    while True :
        # On trie par score descendant, et on prend avec le filtre 56027, qui
        # est le filtre "Everything"
        request = f"https://derpibooru.org/api/v1/json/search/images?filter_id=56027&sf=score&sd=desc&page={page_number}&q={SEARCH_TO_SCAN}"
        response = requests.get( request )
        print( "On demande à Derpibooru : " + request )
        
        json = response.json()
        
        if len( json["images"] ) == 0 :
            print( "On est arrivé au bout de cette recherche !" )
            break
        
        for post in json["images"] :
            url = f"https://derpibooru.org/{post['id']}"
            print( "Requête : " + url )
            
            if LIMIT != None and count > LIMIT :
                print( f"On a atteint la limite de {LIMIT} posts envoyés !" )
            else :
                count += 1
            
            post_artists_launched = []
            for tag in post["tags"] :
                if tag[:7] == "artist:" :
                    if tag in launched_artists :
                        post_artists_launched.append( True )
                    else :
                        launched_artists.append( tag )
                        post_artists_launched.append( False )
            
            if not all( post_artists_launched ) :
                print( "Envoyée !" )
                server.get_request( url )
            else :
                print( "Non envoyée, tous les artistes de ce post sont déjà envoyés !" )
        
        page_number += 1


if __name__ == "__main__" :
    scan_derpibooru_search( "twilight sparkle" )
