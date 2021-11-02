#!/usr/bin/python3
# coding: utf-8

from typing import List
from dateutil import parser
from bs4 import BeautifulSoup

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
    change_wdir( "../.." )
    path.append(get_wdir())

from link_finder.supported_websites.utils.class_Webpage_to_Twitter_Accounts import Webpage_to_Twitter_Accounts
from link_finder.supported_websites.utils.get_with_rate_limits import get_with_rate_limits
from link_finder.supported_websites.utils.validate_url import validate_url


"""
On ne peut pas utiliser directement l'API DeviantArt parce qu'elle est naze.
On ne peut pas retrouver l'objet sur l'API d'une illustration, car il faut son
UUID, et donc forcément analyser la page HTML.
Il y a une librairie sinon :
https://github.com/neighbordog/deviantart

Ceci n'est donc pas vraiment une couche d'abstraction à l'API DeviantArt, mais
plutôt une "bidouille" qui fait parfaitement le travail.
Cette bidouille est insensible au fait que l'illustration soit indiquée comme
"sensible" ou pas.

Cette classe garde en cache le dernier appel à l'API.
Ainsi, afin d'optimiser l'utilisation de cette classe, il faut :
- Initialiser un objet qu'une seule fois pour un thread, et le réutiliser.
- Ne surtout pas partager l'objet entre plusieurs threads.
- Et exécuter les deux méthodes get_image_urls() et get_twitter_accounts() l'une
  après l'autre pour une même illustration (C'est à dire ne pas mélanger les
  illustrations).
"""
class DeviantArt :
    def __init__  ( self ) :
        # On utilise ces attributs pour mettre en cache le résultat de l'appel
        # à l'API pour une illustration.
        # On met en cache car la demande de l'URL de l'image et la demande des
        # URLs des comptes Twitter sont souvent ensembles.
        self._cache_illust_url = None
        self._cache_illust_url_json = None
        self._cache_illust_url_html = None
    
    
    """
    Mettre en cache le résultat de l'appel à l'API de l'illustration si ce
    n'est pas déjà fait.
    Permet de MàJ le cache, si l'URL mène bien vers une illustration.
    
    @param illust_id L'URL de l'illustration DeviantArt.
    @return True si l'URL donnée est utilisable.
            False sinon.
    """
    def _cache_or_get ( self, illust_url : str ) -> bool :
        if illust_url != self._cache_illust_url :
            
            response = get_with_rate_limits( "https://backend.deviantart.com/oembed?url=" + illust_url,
                                             retry_on_those_http_errors = [ 403 ] )
            
            if response.status_code == 404 :
                return False
            json = response.json()
            if json["type"] != "photo" :
                return False
            
            self._cache_illust_url = illust_url
            self._cache_illust_url_json = json
            
            response = get_with_rate_limits( illust_url,
                                             retry_on_those_http_errors = [ 403 ] )
            
            self._cache_illust_url_html = response
        
        return True
    
    """
    Obtenir l'URL de l'image source à partir de l'URL de l'illustration postée.
    
    @param illust_id L'URL de l'illustration DeviantArt.
    @return Liste contenant une ou deux URL de l'image. Si il y en a une, c'est
            l'image redimensionnée. Si il y en a deux, la première est la
            résolution originale de l'image, la seconde est redimensionnée.
            Ou None si il y a  eu un problème, c'est à dire que l'URL donnée
            ne mène pas à une illustration sur DeviantArt.
    """
    def get_image_urls ( self, illust_url  : str ) -> List[str] :
        # On met en cache si ce n'est pas déjà fait
        if not self._cache_or_get( illust_url ) :
            return None
        
        # On va faire de l'analyse HTML avec BeautifulSoup, pour trouver l'URL
        # de l'image en bonne qualité
        soup = BeautifulSoup( self._cache_illust_url_html.text, "html.parser" )
        
        # Coup de bol, la page HTML demande au navigateur de preload l'image
        # dans sa qualité maximale
        objet = soup.find("link", {"rel": "preload", "as": "image"})
        
        # Si on ne trouve rien, c'est que l'image est "mature content" / NSFW,
        # marquée sensible quoi / "adulte"
        # On retourne donc l'image dans le JSON, donc en moins bonne qualité
        # Note : On pourrait faire un système où on passe un jeton d'auth en
        # cookie, comme on le faisait avec GetOldTweets3 et comme on le fait
        # avec SNScrape
        if objet == None :
            return [ self._cache_illust_url_json["url"] ]
        
        # On retourne le résultat voulu
        return [ objet.get("href"),
                 self._cache_illust_url_json["url"] ]
    
    """
    Retourne les noms des comptes Twitter trouvés.
    
    @param illust_url L'URL de l'illustration DeviantArt.
    @param force_deviantart_account_name Forcer le nom du compte DeviantArt
                                         (OPTIONNEL).
    @param multiplexer Méthode "link_mutiplexer()" de la classe "Link_Finder"
                       (OPTIONNEL).
    
    @return Une liste de comptes Twitter.
            Ou une liste vide si aucun URL de compte Twitter valide n'a été
            trouvé.
            Ou None si il y a  eu un problème, c'est à dire que l'URL donnée
            ne mène pas à une illustration sur DeviantArt.
    """
    def get_twitter_accounts ( self, illust_url,
                                     force_deviantart_account_name = None,
                                     multiplexer = None ) -> List[str] :
        twitter_accounts = []
        
        if force_deviantart_account_name == None :
            # On met en cache si ce n'est pas déjà fait
            if not self._cache_or_get( illust_url ) :
                return None
            
            
            # SCAN PAGE DE L'ILLUSTRATION
            
            # Sur DeviantArt, il faut aussi scanner la page où l'illustration a été
            # postée, car certains artistes mettent leur compte Twitter dans la
            # description de leur illustration.
            # On réessaye sur les erreurs 403 données par Cloudfront si on fait
            # trop de requêtes.
            scanner1 = Webpage_to_Twitter_Accounts( illust_url,
                                                    response = self._cache_illust_url_html,
                                                    retry_on_those_http_errors = [ 403 ] )
            
            # PB : Si un petit malin met son compte Twitter en commentaire, il sera
            # considéré comme le compte Twitter de l'artiste.
            # On scan donc qu'une partie de la page !
            scanner1.soup = scanner1.soup.find("div", {"data-hook": "deviation_meta"}).parent
            
            # Rechercher (Désactiver car le multiplexeur les cherche aussi)
            if multiplexer == None :
                twitter_accounts += scanner1.scan()
            
            # Envoyer dans le multiplexer les autres URL qu'on peut trouver
            if multiplexer != None :
                for link in scanner1.scan( validator_function = validate_url ) :
                    get_multiplex = multiplexer( link )
                    if get_multiplex != None :
                        twitter_accounts += get_multiplex
            
            
            # SCAN PAGE "ABOUT" DE L'ARTISTE
            artist_about_page = self._cache_illust_url_json["author_url"] + "/about"
            
            # Si on a le multiplexeur de liens, il vaut mieux passer par lui
            # pour scanner la page "about" de l'artiste, plutôt que de le faire
            # nous-même. Cela permet qu'il enregistre dans son dictionnaire
            # qu'il est bien passé par cette page, et donc empêche d'y
            # passer deux fois.
            if multiplexer != None :
                twitter_accounts += multiplexer( artist_about_page )
                return twitter_accounts
            
            scanner2 = Webpage_to_Twitter_Accounts( artist_about_page )
        
        else :
            scanner2 = Webpage_to_Twitter_Accounts(
                "https://deviantart.com/" + force_deviantart_account_name + "/about" )
        
        # PB : Idem, il y a une section commentaires !
        scanner2.soup = scanner2.soup.find("section", {"id": "about"})
        
        # Rechercher (Désactiver car le multiplexeur les cherche aussi)
        if multiplexer == None :
            twitter_accounts += scanner2.scan()
        
        # Envoyer dans le multiplexer les autres URL qu'on peut trouver
        # On bloque la détection d'un compte DeviantArt, car les artistes ont
        # très très rarement deux comptes DeviantArt, et mettent plutôt des
        # liens vers les pages de leurs ami(e)s
        if multiplexer != None :
            for link in scanner2.scan( validator_function = validate_url ) :
                get_multiplex = multiplexer( link, source = "block_deviantart_account" )
                if get_multiplex != None :
                    twitter_accounts += get_multiplex
        
        
        return twitter_accounts
    
    """
    Obtenir la date de publication de l'illustration.
    
    @param illust_id L'URL de l'illustration DeviantArt.
    @return L'objet datetime de la date de publication de l'image.
            Ou None si il y a  eu un problème, c'est à dire que l'URL donnée
            ne mène pas à une illustration sur DeviantArt.
    """
    def get_datetime ( self, illust_url  : str ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self._cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return parser.isoparse( self._cache_illust_url_json["pubdate"] )


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    da = DeviantArt()
    test = []
    test.append(
        da.get_twitter_accounts(
            "https://www.deviantart.com/nopeys/art/Azula-847851539" ) )
    
    if test == [['NOPEYS1', 'NOPEYS1']] : # Trouve deux fois, plus de filtre
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
        print( test )
