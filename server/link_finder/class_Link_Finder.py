#!/usr/bin/python3
# coding: utf-8

import re

try :
    from supported_websites import DeviantArt, Pixiv, Danbooru, Philomena
    from supported_websites.utils import filter_twitter_accounts_list, Webpage_to_Twitter_Accounts
    from supported_websites.utils import validate_url, validate_deviantart_account_url, validate_pixiv_account_url, validate_twitter_account_url, validate_linktree_account_url
    from class_Link_Finder_Result import Link_Finder_Result, Not_an_URL, Unsupported_Website
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .supported_websites import DeviantArt, Pixiv, Danbooru, Philomena
    from .supported_websites.utils import filter_twitter_accounts_list, Webpage_to_Twitter_Accounts
    from .supported_websites.utils import validate_url, validate_deviantart_account_url, validate_pixiv_account_url, validate_twitter_account_url, validate_linktree_account_url
    from .class_Link_Finder_Result import Link_Finder_Result, Not_an_URL , Unsupported_Website

# Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
import parameters as param


# ^ = Début de la chaine, $ = Fin de la chaine
deviantart_url = re.compile(
    r"^http(?:s)?:\/\/(?:([a-zA-Z0-9]+)\.)?deviantart\.com(?:\/|$)" )
pixiv_url = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?pixiv\.net(?:\/|$)" )
danbooru_url = re.compile(
    r"^http(?:s)?:\/\/danbooru\.donmai\.us(?:\/|$)" )
derpibooru_url = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?derpibooru\.org(?:\/|$)" )
furbooru_url = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?furbooru\.org(?:\/|$)" )

# Bien mettre (?:\/|$) au bout pour s'assurer qu'il y a un "/" ou qu'on est à
# la fin de la chaine. Permet d'éviter de passer des sous domaines. Par exemple
# deviantart.com.example.tld, ce qui pourrait être une faille de sécurité.


"""
Moteur de recherche des comptes Twitter d'un artiste, à partir d'une
illustration postée sur l'un des sites supportés.

Les objets utilisés par cette classe gardent en cache leur dernier appel à
leurs API.
Ainsi, afin d'optimiser l'utilisation de cette classe, il faut :
- Initialiser un objet qu'une seule fois pour un thread, et le réutiliser.
- Ne surtout pas partager l'objet entre plusieurs threads.
- Et exécuter les deux méthodes get_image_url() et get_twitter_accounts() l'une
  après l'autre pour une même illustration (C'est à dire ne pas mélanger les
  illustrations).

Note importante : Si la source d'une image est un Tweet, ne jamais être tenté
de prendre le compte qui l'a posté pour le compte Twitter de l'artiste !
"""
class Link_Finder :
    def __init__ ( self ) :
        self.deviantart = DeviantArt()
        self.pixiv = Pixiv( param.PIXIV_USERNAME, param.PIXIV_PASSWORD )
        self.danbooru = Danbooru()
        self.derpibooru = Philomena( site_ID = 1 )
        self.furbooru = Philomena( site_ID = 2 )
    
    """
    @param illust_url L'URL d'une illustration postée sur l'un des sites
                      supportés.
    @param TWITTER_ONLY Ne retourner dans l'objet que les comptes Twitter
                        (OPTIONNEL).
    
    @return Un objet "Link_Finder_Result" contenant les attributs suivants :
            - image_url : L'URL de l'image.
            - twitter_accounts : Une liste de comptes Twitter, ou une liste 
              vide si aucun URL de compte Twitter valide n'a été trouvé.
            - publish_date : L'objet datetime de la date de publication de
              l'image.
    
            Ou None si l'URL est invalide (Mais que le site est supporté),
            c'est à dire que l'URL donnée ne mène pas à une illustration.
            
            Afin d'optimiser, si aucune compte Twitter n'a été trouvé,
            "image_url" et "publish_date" sont à None.

    Attention : Cette méthode émet des exceptions Unsupported_Website si le
    site n'est pas supporté !
    """
    def get_data ( self, illust_url : str, TWITTER_ONLY = False ) -> Link_Finder_Result :
        # Ce sont les clases qui analysent les URL et vont dire si elles
        # mènent bien vers des illustrations.
        # Ici, on vérifie juste le domaine.
        
        # Vérification que ce soit bien une URL
        if validate_url( illust_url ) == None :
            raise Not_an_URL
        
        # ====================================================================
        # DEVIANTART
        # ====================================================================
        elif re.match( deviantart_url, illust_url ) != None :
            twitter_accounts = self.deviantart.get_twitter_accounts( illust_url, 
                                                                     multiplexer = self.link_mutiplexer )
            if not TWITTER_ONLY and twitter_accounts != [] and twitter_accounts != None :
                image_url = self.deviantart.get_image_url( illust_url )
                publish_date = self.deviantart.get_datetime( illust_url )
        
        # ====================================================================
        # PIXIV
        # ====================================================================
        elif re.match( pixiv_url, illust_url ) != None :
            twitter_accounts = self.pixiv.get_twitter_accounts( illust_url )
            if not TWITTER_ONLY and twitter_accounts != [] and twitter_accounts != None :
                image_url = self.pixiv.get_image_url( illust_url )
                publish_date = self.pixiv.get_datetime( illust_url )
        
        # ====================================================================
        # DANBOORU
        # ====================================================================
        elif re.match( danbooru_url, illust_url ) != None :
            twitter_accounts = self.danbooru.get_twitter_accounts( illust_url,
                                                                   multiplexer = self.link_mutiplexer )
            if not TWITTER_ONLY and twitter_accounts != [] and twitter_accounts != None :
                image_url = self.danbooru.get_image_url( illust_url )
                publish_date = self.danbooru.get_datetime( illust_url )
        
        # ====================================================================
        # DERPIBOORU
        # ====================================================================
        elif re.match( derpibooru_url, illust_url ) != None :
            twitter_accounts = self.derpibooru.get_twitter_accounts( illust_url,
                                                                     multiplexer = self.link_mutiplexer,
                                                                     loopback_source = self.get_data,
                                                                     already_loopback = TWITTER_ONLY )
            if not TWITTER_ONLY and twitter_accounts != [] and twitter_accounts != None :
                image_url = self.derpibooru.get_image_url( illust_url )
                publish_date = self.derpibooru.get_datetime( illust_url )
        
        # ====================================================================
        # FURBOORU
        # ====================================================================
        elif re.match( furbooru_url, illust_url ) != None :
            twitter_accounts = self.furbooru.get_twitter_accounts( illust_url,
                                                                   multiplexer = self.link_mutiplexer,
                                                                   loopback_source = self.get_data,
                                                                   already_loopback = TWITTER_ONLY )
            if not TWITTER_ONLY and twitter_accounts != [] and twitter_accounts != None :
                image_url = self.furbooru.get_image_url( illust_url )
                publish_date = self.furbooru.get_datetime( illust_url )
        
        # ====================================================================
        # Site non supporté
        # ====================================================================
        else :
            raise Unsupported_Website
        
        # ====================================================================
        # Retourner
        # ====================================================================
        
        # Le site est supporté mais l'URL ne mène pas à une illustration
        if twitter_accounts == None :
            return None
        
        if TWITTER_ONLY or twitter_accounts == [] :
            image_url = None
            publish_date = None
        
        # Le site est supporté et l'URL mène à une illustration
        # La liste des comptes Twitter trouvés peut alors être vide
        return Link_Finder_Result( image_url,
                                   filter_twitter_accounts_list( twitter_accounts ),
                                   publish_date )
    
    
    """
    Rechercher des comptes Twitter dans des formats de pages webs connus.
    Par exemple, un profil DeviantArt, un profil Pixiv, ou un profil Linktree.
    Si l'URL est reconnue comme celle d'un compte Twitter, le compt sera
    retourné.
    
    @param url URL de la page web à analyser.
    @param source Nom du site source. Voir le code ci-dessous.
                  Pour éviter de reboucler
    
    @return Liste de comptes Twitter.
            Ou None si la page web est inconnue.
    """
    def link_mutiplexer ( self, url, source = "" ) :
        # Attention : Ne pas donner cette méthode en tant que "multiplexer" aux
        # méthodes "get_twitter_accounts()", sinon on risque de créer des
        # boucles infinies !
        
        # TWITTER
        twitter = validate_twitter_account_url( url ) # Ne retourne pas de liste
        if twitter != None :
            return [ twitter ]
        
        # DEVIANTART
        if source != "deviantart" :
            deviantart = validate_deviantart_account_url( url )
            if deviantart != None :
                return self.deviantart.get_twitter_accounts( "", force_deviantart_account_name = deviantart )
        
        # PIXIV
        if source != "pixiv" :
            pixiv = validate_pixiv_account_url( url )
            if pixiv != None :
                return self.pixiv.get_twitter_accounts( "", force_pixiv_account_id = pixiv )
        
        # LINKTREE
        linktree = validate_linktree_account_url( url )
        if linktree != None :
            scanner = Webpage_to_Twitter_Accounts( "https://linktr.ee/" + linktree )
            return scanner.scan()
        
        # PAGE NON SUPPORTEE
        return None


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    import link_finder_tester
