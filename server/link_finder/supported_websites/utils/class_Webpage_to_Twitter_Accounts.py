#!/usr/bin/python3
# coding: utf-8

import re
from bs4 import BeautifulSoup
from typing import List

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendemment (Notemment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    from os import getcwd as get_wdir
    from sys import path
    change_wdir(get_dirname(get_abspath(__file__)))
    change_wdir( "../../.." )
    path.append(get_wdir())

from link_finder.supported_websites.utils.validate_twitter_account_url import validate_twitter_account_url
from link_finder.supported_websites.utils.get_with_rate_limits import get_with_rate_limits


"""
Scanne une page web à la recherche de comptes Twitter.

Cette classe peut chercher autre chose que des comptes Twitter, avec une
fonction similaire à "validate_twitter_account_url".

Mis sous la forme d'un objet afin de pouvoir modifier la sélection de
BeautifulSoup avant de lancer le scan.
Cela permer de scanner qu'une partie de la page !

Exemple :
    scanner = Webpage_to_Twitter_Accounts( "http://domain.tld/page.html" )
    scanner.soup = object.soup.find( "div", {"id": "un-id-de-div"} )
    liste = scanner.scan()
"""
class Webpage_to_Twitter_Accounts :
    """
    @param url L'URL de la page web à scanner.
    @param response Si vous avez déjo fait le GET, donnez-moi la réponse.
                    Même format que ce que retourne la fonction
                    get_with_rate_limits().
                    (OPTIONNEL)
    @param USE_BS4 Scanner uniquement les balises HTML <a href=""> avec
                   BeautifulSoup4.
                   Si mis sur False, Régex est utilisé, ce qui permet de
                   trouver toutes les URL dans le code de la page.
                   (OPTIONNEL)
    @param retry_on_those_http_errors Liste d'erreurs HTTP sur lesquelles on
                                      réessaye.
    """
    def __init__ ( self,
                   url : str,
                   response = None,
                   USE_BS4 : bool = True,
                   retry_on_those_http_errors = [] ) :
        # Prendre le code HTML de la page
        if response == None :
            self.response = get_with_rate_limits( url, retry_on_those_http_errors = retry_on_those_http_errors )
        else :
            self.response = response
        
        # Initialiser BeautifulSoup si besoin
        if USE_BS4 :
            self.soup = BeautifulSoup( self.response.text, "html.parser" )
        self.USE_BS4 = USE_BS4
    
    """
    @param validator_function Fonction valide une URL comme l'URL d'un compte,
                              et retourne l'identifiant de ce compte.
                              Permet de chercher autre chose que des comptes
                              Twitter.
                              (OPTIONNEL)
    @return La liste des comptes Twitter trouvés.
            Ou None si il y a un problème avec l'URL.
            Peut retourner une liste vide si aucun compte Twitter n'a été
            trouvé.
    """
    def scan ( self, validator_function = validate_twitter_account_url ) -> List[str] :
        # Scan avec BeautifulSoup4
        if self.USE_BS4  :
            accounts_found = self._scan_beautifulsoup( validator_function )
        
        # Scan avec Regex
        else :
            accounts_found = self._scan_regex( validator_function )
        
        # Filtrer (Supprimer les doublons et les comptes officiels) et retourner
        return accounts_found
    
    """
    Méthode privée, appelée par la méthode "scan()".
    """
    def _scan_beautifulsoup ( self, validator_function ) -> List[str] :
        # Initialiser la liste que l'on va retourner
        accounts_found : List[str] = []
        
        # Pour trouver toutes les balises HTML <a href=""> trouvables dans la page
        if self.soup != None :
            for link in self.soup.findAll( "a" ) :
                href = link.get("href")
                if href == None :
                    continue
                result = validator_function( link.get("href") )
                if result != None :
                    accounts_found.append( result )
        
        # Retourner
        return accounts_found
    
    """
    Méthode privée, appelée par la méthode "scan()".
    """
    def _scan_regex ( self, validator_function ) -> List[str] :
        # Initialiser la liste que l'on va retourner
        accounts_found : List[str] = []
        
        # Pour trouver toutes les URL trouvables dans la page
        for link in re.findall( r"(https?://[^\s]+)", self.response.text) :
            if link == None :
                continue
            result = validator_function( link )
            if result != None :
                accounts_found.append( result )
        
        # Retourner
        return accounts_found


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    test = []
    
    scanner = Webpage_to_Twitter_Accounts(
        "https://www.deviantart.com/nopeys/art/Azula-847851539" )
    # Pour une page d'illustration DeviantArt
    scanner.soup = scanner.soup.find("div", {"data-hook": "deviation_meta"}).parent
    test.append( scanner.scan() )
    
    scanner = Webpage_to_Twitter_Accounts(
        "https://www.deviantart.com/sniffsniffs/about" )
    # Pour une page "About" d'un compte DeviantArt
    scanner.soup = scanner.soup.find("section", {"id": "about"})
    test.append( scanner.scan() )
    
    scanner = Webpage_to_Twitter_Accounts(
        "https://www.deviantart.com/sniffsniffs/about",
        USE_BS4 = False ) # Ce n'est pas recommandé d'utiliser Régex pour DA !
    test.append( scanner.scan() )
    
    if test == [['NOPEYS1'], ['lumspark'], ['lumspark', 'DeviantArt']] : # Bordel car plus de filtre
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
        print( test )
