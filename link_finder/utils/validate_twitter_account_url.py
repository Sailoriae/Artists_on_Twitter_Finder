#!/usr/bin/python3
# coding: utf-8

import re


twitter_account_name_regex = re.compile(
    "http(?:s)?:\/\/(?:www\.)?twitter\.com\/(?:#!\/)?(?:@)?([a-zA-Z0-9_]+)(?:\/)?" )
# ^ = Début de la chaine, $ = Fin de la chaine
twitter_account_name_regex_strict = re.compile(
    "^http(?:s)?:\/\/(?:www\.)?twitter\.com\/(?:#!\/)?(?:@)?([a-zA-Z0-9_]+)(?:\/)?$" )
    
"""
Est ce que cet URL est l'URL d'un compte Twitter ?
@param url L'URL à examiner
@param STRICT True pour que l'URL corresponde exactement
              False si l'URL peut-être contenue dans la chaine passée
              Cela peut être intéressant si on veut scanner une URL de
              redirection, contenant l'URL du compte Twitter
              (OPTIONNEL)
@return Le nom d'utilisateur du compte Twitter
        Ou None si ce n'est pas un compte Twitter
"""
def validate_twitter_account_url ( url : str, STRICT : bool = True ) -> str :
    if STRICT :
        result = re.search( twitter_account_name_regex_strict, url )
    else :
        result = re.search( twitter_account_name_regex, url )
    if result == None :
        return None
    return result.group( 1 )


"""
Test du bon fonctionnement de cette fonction
"""
if __name__ == '__main__' :
    test = []
    test.append( validate_twitter_account_url( "https://twitter.com/@jack" ) )
    test.append( validate_twitter_account_url( "https://twitter.com/jack" ) )
    test.append( validate_twitter_account_url( "https://twitter.com/#!/jack" ) )
    test.append( validate_twitter_account_url( "https://twitter.com/jack/" ) )
    test.append( validate_twitter_account_url( "https://twitter.com" ) )
    
    if test == ['jack', 'jack', 'jack', 'jack', None] :
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
