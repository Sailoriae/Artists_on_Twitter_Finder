#!/usr/bin/python3
# coding: utf-8

import re

try :
    from supported_websites import DeviantArt
    from supported_websites import Pixiv
    from supported_websites import Danbooru
    from supported_websites import Philomena
    from supported_websites.utils import filter_twitter_accounts_list
    from class_Link_Finder_Result import Link_Finder_Result, Not_an_URL, Unsupported_Website
except ModuleNotFoundError : # Si on a été exécuté en temps que module
    from .supported_websites import DeviantArt
    from .supported_websites import Pixiv
    from .supported_websites import Danbooru
    from .supported_websites import Philomena
    from .supported_websites.utils import filter_twitter_accounts_list
    from .class_Link_Finder_Result import Link_Finder_Result, Not_an_URL , Unsupported_Website

# Ajouter le répertoire parent au PATH pour pouvoir importer les paramètres
from sys import path as sys_path
from os import path as os_path
sys_path.append(os_path.dirname(os_path.dirname(os_path.abspath(__file__))))
import parameters as param


#twitter_url = re.compile(
#    "http(?:s)?:\/\/(?:www\.)?twitter\.com" )

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

# Source :
# https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
url = re.compile(
    r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b([-a-zA-Z0-9@:%_\+.~#?&\/=]*)$" )


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

    Attention : Cette méthode émet des exceptions Unsupported_Website si le
    site n'est pas supporté !
    """
    def get_data ( self, illust_url : str, TWITTER_ONLY = False ) -> str :
        # Ce sont les clases qui analysent les URL et vont dire si elles
        # mènent bien vers des illustrations.
        # Ici, on vérifie juste le domaine.
        
        # Vérification que ce soit bien une URL
        if re.search( url, illust_url ) == None :
            raise Not_an_URL
        
        # ====================================================================
        # DEVIANTART
        # ====================================================================
        elif re.search( deviantart_url, illust_url ) != None :
            twitter_accounts = self.deviantart.get_twitter_accounts( illust_url )
            if not TWITTER_ONLY :
                image_url = self.deviantart.get_image_url( illust_url )
                publish_date = self.deviantart.get_datetime( illust_url )
        
        # ====================================================================
        # PIXIV
        # ====================================================================
        elif re.search( pixiv_url, illust_url ) != None :
            twitter_accounts = self.pixiv.get_twitter_accounts( illust_url )
            if not TWITTER_ONLY :
                image_url = self.pixiv.get_image_url( illust_url )
                publish_date = self.pixiv.get_datetime( illust_url )
        
        # ====================================================================
        # DANBOORU
        # ====================================================================
        elif re.search( danbooru_url, illust_url ) != None :
            twitter_accounts = self.danbooru.get_twitter_accounts( illust_url )
            
            # Si l'URL n'est pas invalide
            if twitter_accounts != None :
                # Pour beaucoup d'artistes sur Danbooru, on peut trouver leur
                # compte Pixiv, et donc s'assurer de touver leurs comptes Twitter.
                pixiv_accounts = self.danbooru.get_pixiv_accounts( illust_url )
                if pixiv_accounts != None :
                    for pixiv_account in pixiv_accounts :
                        accounts = self.pixiv.get_twitter_accounts(
                            None,
                            force_pixiv_account_id = pixiv_account )
                        if accounts != None :
                            twitter_accounts += accounts
            
            if not TWITTER_ONLY :
                image_url = self.danbooru.get_image_url( illust_url )
                publish_date = self.danbooru.get_datetime( illust_url )
        
        # ====================================================================
        # DERPIBOORU
        # ====================================================================
        elif re.search( derpibooru_url, illust_url ) != None :
            twitter_accounts = self.derpibooru.get_twitter_accounts( illust_url )
            
            # Comme les Boorus sont des sites de reposts, on peut trouver la
            # source de l'illustration. Si c'est sur un site que l'on supporte,
            # le Link Finder peut aller y faire un tour !
            source = self.derpibooru.get_source( illust_url )
            if source != None and source != "" :
                try :
                    data = self.get_data( source, TWITTER_ONLY = True )
                except ( Unsupported_Website, Not_an_URL ) :
                    pass
                else :
                    if data != None :
                        twitter_accounts += data.twitter_accounts
            
            if not TWITTER_ONLY :
                image_url = self.derpibooru.get_image_url( illust_url )
                publish_date = self.derpibooru.get_datetime( illust_url )
        
        # ====================================================================
        # FURBOORU
        # ====================================================================
        elif re.search( furbooru_url, illust_url ) != None :
            twitter_accounts = self.furbooru.get_twitter_accounts( illust_url )
            
            # Comme les Boorus sont des sites de reposts, on peut trouver la
            # source de l'illustration. Si c'est sur un site que l'on supporte,
            # le Link Finder peut aller y faire un tour !
            source = self.furbooru.get_source( illust_url )
            if source != None and source != "" :
                try :
                    data = self.get_data( source, TWITTER_ONLY = True )
                except ( Unsupported_Website, Not_an_URL ) :
                    pass
                else :
                    if data != None :
                        twitter_accounts += data.twitter_accounts
            
            if not TWITTER_ONLY :
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
        
        if TWITTER_ONLY :
            image_url = None
            publish_date = None
        
        # Le site est supporté et l'URL mène à une illustration
        # La liste des comptes Twitter trouvés peut alors être vide
        return Link_Finder_Result( image_url,
                                   filter_twitter_accounts_list( twitter_accounts ),
                                   publish_date )


"""
Test du bon fonctionnement de cette classe
"""
if __name__ == '__main__' :
    import link_finder_tester
