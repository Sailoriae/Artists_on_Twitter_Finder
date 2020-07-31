#!/usr/bin/python3
# coding: utf-8

from typing import List
from datetime import datetime


"""
Classe contenant uniquement les données trouvées par le Link Finder.
"""
class Link_Finder_Result :
    def __init__ ( self, image_url : str,
                         twitter_accounts : List[str],
                         publish_date : datetime ) :
        self.image_url = image_url
        self.twitter_accounts = twitter_accounts
        self.publish_date = publish_date


"""
Exception si le site n'est pas supporté.
"""
class Unsupported_Website ( Exception ) :
    pass
