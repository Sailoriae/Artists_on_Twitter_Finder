#!/usr/bin/python3
# coding: utf-8

import re


# ^ = Début de la chaine, $ = Fin de la chaine

# Nouveau format : deviantart.com/artiste
deviantart_account_name_regex_new = re.compile(
    r"(?:http(?:s)?:\/\/)?(?:www\.)?deviantart\.com\/([a-zA-Z0-9]+)" )

# Ancien format : artiste.deviantart.com
deviantart_account_name_regex_old = re.compile(
    r"(?:http(?:s)?:\/\/)?(?:([a-zA-Z0-9]+)\.)deviantart\.com" )


# Attention : Certaines URL peuvent être des URL de redirection. Ainsi, la
# chaine peut être plus grande et contenir l'URL en tant que sous-chaine.
# On ne marque donc pas le début ni la fin de la chaine, et on utilise
# la fonction re.search() !

# Le "http://" ou "https://" est obtionnel.


"""
Est ce que cet URL est l'URL d'un compte DeviantArt ?

@param url L'URL à examiner
@return Le nom d'utilisateur du compte DeviantArt
        Ou None si ce n'est pas un compte DeviantArt
"""
def validate_deviantart_account_url ( url : str ) -> str :
    result_new = re.search( deviantart_account_name_regex_new, url )
    result_old = re.search( deviantart_account_name_regex_old, url )
    if result_new != None : result = result_new.group( 1 )
    elif result_old != None : result = result_old.group( 1 )
    else : return None
    
    if result in [ "tag", "art", "users" ] : # Supprimer les faux-positifs connus
        return None
    else :
        return result


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
