#!/usr/bin/python3
# coding: utf-8

import re


# Source :
# https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
url_regex = re.compile(
    r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b([-a-zA-Z0-9@:%_\+.~#?&\/=]*)$" )


"""
Est ce que cette chaine est une URL

@param url L'URL à examiner
@return La même URL
        Ou None si ce n'est pas une URL
"""
def validate_url ( url : str ) -> str :
    result = re.search( url_regex, url )
    if result != None : return url
    return None
