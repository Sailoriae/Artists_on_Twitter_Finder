#!/usr/bin/python3
# coding: utf-8

import requests
from time import sleep

from class_WebAPI_Client import WebAPI_Client


"""
Fonction permettant de populer la base de données autour d'un tag sur Danbooru.
"""
def scan_danbooru_tag ( TAG_TO_SCAN ) :
    server = WebAPI_Client()
    if not server.ready :
        return
    
    # Liste des artistes déjà envoyé, ça ne sert à rien de faire une autre
    # requête au serveur pour cet artiste, puisqu'on veut juste populer sa
    # base de données
    launched_artists = []
    
    page_number = 1
    last_post_id = None
    while True :
        if page_number <= 1000 :
            response = requests.get(
                "https://danbooru.donmai.us/posts.json?page=" + str(page_number) + "&tags=" + TAG_TO_SCAN )
            print( "On demande à Danbooru : https://danbooru.donmai.us/posts.json?page=" + str(page_number) + "&tags=" + TAG_TO_SCAN )
        else : # A partir de la page 1000, on ne peut plus utiliser les pages, mais l'ID du dernier post
            response = requests.get(
                "https://danbooru.donmai.us/posts.json?page=b" + str(last_post_id) + "&tags=" + TAG_TO_SCAN )
            print( "On demande à Danbooru : https://danbooru.donmai.us/posts.json?page=b" + str(last_post_id) + "&tags=" + TAG_TO_SCAN )
        
        json = response.json()
        
        try :
            if json["success"] == False :
                sleep( 10 )
                continue
        except ( KeyError, TypeError ) :
            pass
        
        for post in json :
            try :
                print( "Requête : https://danbooru.donmai.us/posts/" + str(post["id"]) )
                last_post_id = str(post["id"])
                if not post["tag_string_artist"] in launched_artists :
                    print( "Envoyée ! Artiste : " + post["tag_string_artist"] )
                    server.get_request( "https://danbooru.donmai.us/posts/" + str(post["id"]) )
                    launched_artists.append( post["tag_string_artist"] )
                else :
                    print( "Non envoyée, artiste déjà envoyé : " + post["tag_string_artist"] )
            except KeyError : # Certains posts dans la recherche ont leur ID masqué
                pass
        
        page_number += 1
        
        if len(json) == 0 :
            break
        
        sleep( 60 )


if __name__ == "__main__" :
    scan_danbooru_tag( "hatsune_miku" )
