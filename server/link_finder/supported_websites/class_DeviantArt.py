#!/usr/bin/python3
# coding: utf-8

from typing import List
from datetime import datetime
from bs4 import BeautifulSoup

try :
    from utils import Webpage_to_Twitter_Accounts
    from utils import get_with_rate_limits
except ImportError : # Si on a été exécuté en temps que module
    from .utils import Webpage_to_Twitter_Accounts
    from .utils import get_with_rate_limits


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
- Et exécuter les deux méthodes get_image_url() et get_twitter_accounts() l'une
  après l'autre pour une même illustration (C'est à dire ne pas mélanger les
  illustrations).
"""
class DeviantArt :
    def __init__  ( self ) :
        # On utilise ces attributs pour mettre en cache le résultat de l'appel
        # à l'API pour une illustration.
        # On met en cache car la demande de l'URL de l'image et la demande des
        # URLs des comptes Twitter sont souvent ensembles.
        self.cache_illust_url = None
        self.cache_illust_url_json = None
    
    
    """
    METHODE PRIVEE, NE PAS UTILISER !
    Mettre en cache le résultat de l'appel à l'API de l'illustration si ce
    n'est pas déjà fait.
    Permet de MàJ le cache, si l'URL mène bien vers une illustration.
    
    @param illust_id L'URL de l'illustration DeviantArt.
    @return True si l'URL donnée est utilisable.
            False sinon.
    """
    def cache_or_get ( self, illust_url : str ) -> bool :
        if illust_url != self.cache_illust_url :
            
            response = get_with_rate_limits( "https://backend.deviantart.com/oembed?url=" + illust_url,
                                             retry_on_those_http_errors = [ 403 ] )
            
            if response.status_code == 404 :
                return False
            json = response.json()
            if json["type"] != "photo" :
                return False
            
            self.cache_illust_url = illust_url
            self.cache_illust_url_json = json
        
        return True
    
    """
    Obtenir l'URL de l'image source à partir de l'URL de l'illustration postée.
    
    @param illust_id L'URL de l'illustration DeviantArt.
    @return L'URL de l'image.
            Ou None si il y a  eu un problème, c'est à dire que l'URL donnée
            ne mène pas à une illustration sur DeviantArt.
    """
    def get_image_url ( self, illust_url  : str ) -> str :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        # On va faire de l'analyse HTML avec BeautifulSoup, pour trouver l'URL
        # de l'image en bonne qualité
        response = get_with_rate_limits( illust_url, retry_on_those_http_errors = [ 403 ] )
        soup = BeautifulSoup( response.text, "html.parser" )
        
        # Coup de bol, la page HTML demande au navigateur de preload l'image
        # dans sa qualité maximale
        objet = soup.find("link", {"rel": "preload", "as": "image"})
        
        # Si on ne trouve rien, c'est que l'image est "mature content" / NSFW,
        # marquée sensible quoi / "adulte"
        # On retourne donc l'image dans le JSON, donc en moins bonne qualité
        # Note : On pourrait faire un système où on passe un jeton d'auth en
        # cookie, comme on le fait avec GetOldTweets3
        if objet == None :
            return self.cache_illust_url_json["url"]
        
        # On retourne le résultat voulu
        return objet.get("href")
    
    """
    Retourne les noms des comptes Twitter trouvés.
    
    @param illust_url L'URL de l'illustration DeviantArt.
    @return Une liste de comptes Twitter.
            Ou une liste vide si aucun URL de compte Twitter valide n'a été
            trouvé.
            Ou None si il y a  eu un problème, c'est à dire que l'URL donnée
            ne mène pas à une illustration sur DeviantArt.
    """
    def get_twitter_accounts ( self, illust_url ) -> List[str] :
        # On met en cache si ce n'est pas déjà fait
        if not self.cache_or_get( illust_url ) :
            return None
        
        twitter_accounts = []
        
        
        # SCAN PAGE DE L'ILLUSTRATION
        
        # Sur DeviantArt, il faut aussi scanner la page où l'illustration a été
        # postée, car certains artistes mettent leur compte Twitter dans la
        # description de leur illustration.
        # On réessaye sur les erreurs 403 données par Cloudfront si on fait
        # trop de requêtes.
        scanner1 = Webpage_to_Twitter_Accounts( illust_url,
                                                retry_on_those_http_errors = [ 403 ] )
        
        # PB : Si un petit malin met son compte Twitter en commentaire, il sera
        # considéré comme le compte Twitter de l'artiste.
        # On scan donc qu'une partie de la page !
        scanner1.soup = scanner1.soup.find("div", {"data-hook": "deviation_meta"}).parent
        
        twitter_accounts += scanner1.scan()
        
        
        # SCAN PAGE "ABOUT" DE L'ARTISTE
        
        scanner2 = Webpage_to_Twitter_Accounts(
            self.cache_illust_url_json["author_url"] + "/about" )
        
        # PB : Idem, il y a une section commentaires !
        scanner2.soup = scanner2.soup.find("section", {"id": "about"})
        
        twitter_accounts += scanner2.scan()
        
        
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
        if not self.cache_or_get( illust_url ) :
            return None
        
        # On retourne le résultat voulu
        return datetime.fromisoformat( self.cache_illust_url_json["pubdate"] )


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    da = DeviantArt()
    test = []
    test.append(
        da.get_twitter_accounts(
            "https://www.deviantart.com/nopeys/art/Azula-847851539" ) )
    
    if test == [['nopeys1', 'nopeys1']] : # Trouve deux fois, plus de filtre
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
        print( test )
