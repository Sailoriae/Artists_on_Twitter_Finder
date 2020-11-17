#!/usr/bin/python3
# coding: utf-8

import re


url_regex = re.compile(
    r"(?:http(?:s)?:\/\/)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b\/" )

# Le "http://" ou "https://" est optionnel.
# Ne valide que le NDD et le protocole, la suite c'est trop complexe.


"""
Est ce que cette chaine est une URL

@param url L'URL à examiner
@return La même URL
        Ou None si ce n'est pas une URL
"""
def validate_url ( url : str ) -> str :
    result = re.match( url_regex, url ) # re.match() ici, et pas re.search()
    if result != None : return url
    return None
