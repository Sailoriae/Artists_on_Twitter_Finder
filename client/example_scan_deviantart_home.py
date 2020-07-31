#!/usr/bin/python3
# coding: utf-8

import requests
from time import sleep

from class_WebAPI_Client import WebAPI_Client


"""
Fonction permettant de populer la base de données à partir de la page d'accueil
de DeviantArt.
"""
def scan_deviantart_hoome ( NUMBER_OF_ILLUST_TO_SEND ) :
    server = WebAPI_Client()
    if not server.ready :
        return
    
    page_number = 0
    deviations_count = 0
    while True :
        request = "https://www.deviantart.com/_napi/da-browse/api/faceted?init=false&page_type=browse_home&order=recommended&include_scraps=false&offset=" + str( page_number * 48 )
        print( "On demande à DeviantArt : " + request )
        response = requests.get( request )
        
        json = response.json()
        
        for deviation in json["deviations"] :
            print( "Requête : " + deviation["url"] )
            server.get_request( deviation["url"] )
            deviations_count += 1
            
            if deviations_count > NUMBER_OF_ILLUST_TO_SEND :
                return
        
        if json["hasMore"] :
            page_number += 1
        else :
            return
        
        sleep( 60 )


if __name__ == "__main__" :
    scan_deviantart_hoome( 150 )
