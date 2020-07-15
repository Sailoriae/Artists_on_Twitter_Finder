#!/usr/bin/python3
# coding: utf-8

import re


# ^ = Début de la chaine, $ = Fin de la chaine

# Nouveau format : deviantart.com/artiste
new_deviantart_account_name_regex = re.compile(
    "http(?:s)?:\/\/(?:www\.)?deviantart\.com\/([a-zA-Z0-9]+)(?:\/)?" )
new_deviantart_account_name_regex_strict = re.compile(
    "^http(?:s)?:\/\/(?:www\.)?deviantart\.com\/([a-zA-Z0-9]+)(?:\/)?$" )

# Ancien format : artiste.deviantart.com
old_deviantart_account_name_regex = re.compile(
    "http(?:s)?:\/\/(?:([a-zA-Z0-9]+)\.)deviantart\.com(?:\/)?" )
old_deviantart_account_name_regex_strict = re.compile(
    "^http(?:s)?:\/\/(?:([a-zA-Z0-9]+)\.)deviantart\.com(?:\/)?$" )

"""
Est ce que cet URL est l'URL d'un compte DeviantArt ?
@param url L'URL à examiner
@param STRICT True pour que l'URL corresponde exactement
              False si l'URL peut-être contenue dans la chaine passée
              Cela peut être intéressant si on veut scanner une URL de
              redirection, contenant l'URL du compte Twitter
              (OPTIONNEL)
@return Le nom d'utilisateur du compte DeviantArt
        Ou None si ce n'est pas un compte DeviantArt
"""
def validate_deviantart_account_url ( url : str, STRICT : bool = True ) -> str :
    if STRICT :
        result_new = re.match( new_deviantart_account_name_regex_strict, url )
        result_old = re.match( old_deviantart_account_name_regex_strict, url )
    else :
        result_new = re.match( new_deviantart_account_name_regex, url )
        result_old = re.match( old_deviantart_account_name_regex, url )
    if result_new != None :
        return result_new.group( 1 )
    if result_old != None :
        return result_old.group( 1 )
    return None


"""
Test du bon fonctionnement de cette fonction
"""
if __name__ == '__main__' :
    test = []
    test.append( validate_deviantart_account_url( "https://mauroz.deviantart.com/" ) )
    test.append( validate_deviantart_account_url( "https://mauroz.deviantart.com" ) )
    test.append( validate_deviantart_account_url( "https://www.deviantart.com/mauroz" ) )
    test.append( validate_deviantart_account_url( "https://deviantart.com/mauroz/" ) )
    test.append( validate_deviantart_account_url( "https://deviantart.com" ) )
    
    if test == ['mauroz', 'mauroz', 'mauroz', 'mauroz', None] :
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
