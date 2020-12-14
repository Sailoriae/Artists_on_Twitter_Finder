#!/usr/bin/python3
# coding: utf-8

import requests

from class_AOTF_Client import AOTF_Client


"""
Fonction permettant de populer la base de données à partir de la page d'accueil
de DeviantArt, ou d'une recherche.
Pour la recherche, les résultats sont triés par "Popular all times".

@param NUMBER_OF_ILLUST_TO_SEND Nombre d'illustrations à envoyer au serveur.
@param SEARCH Recherche DeviantArt à scanner, si ce n'est pas un scan de la
              page d'accueil. Laisser à "None" pour scanner la page d'accueil.
"""
def scan_deviantart_home_or_search ( NUMBER_OF_ILLUST_TO_SEND = 150, SEARCH = None ) :
    server = AOTF_Client()
    if not server.ready :
        return
    
    page_number = 0
    deviations_count = 0
    while True :
        if SEARCH != None:
            request = f"https://www.deviantart.com/_napi/da-browse/api/faceted?init=false&page_type=browse_home&order=popular-all-time&include_scraps=false&offset={page_number * 48 }&q={SEARCH}"
        else :
            request = f"https://www.deviantart.com/_napi/da-browse/api/faceted?init=false&page_type=browse_home&order=recommended&include_scraps=false&offset={page_number * 48 }"
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


if __name__ == "__main__" :
    # Scan de la page d'acceuil de DeviantArt
    scan_deviantart_home_or_search()
