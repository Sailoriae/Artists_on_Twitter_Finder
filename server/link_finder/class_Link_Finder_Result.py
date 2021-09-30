#!/usr/bin/python3
# coding: utf-8

from typing import List
from datetime import datetime


"""
Classe contenant uniquement les données trouvées par le Link Finder.
Un objet de cette classe est retournée par le Link Finder pour son utilisation.
"""
class Link_Finder_Result :
    def __init__ ( self, image_urls : List[str],
                         twitter_accounts : List[str],
                         publish_date : datetime ) :
        self.image_urls = image_urls
        self.twitter_accounts = twitter_accounts
        self.publish_date = publish_date


"""
Exception si l'entrée n'est pas une URL.
"""
class Not_an_URL ( Exception ) :
    pass

"""
Exception si le site n'est pas supporté.
"""
class Unsupported_Website ( Exception ) :
    pass
