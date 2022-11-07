#!/usr/bin/python3
# coding: utf-8

import re


# ^ = Début de la chaine, $ = Fin de la chaine
# Ne pas marquer le début ni la fin !
caard_account_name_regex = re.compile(
    r"(?:http(?:s)?:\/\/)?([a-z0-9\-]{3,})\.((?:carrd\.co)|(?:crd\.co)|(?:uwu\.ai))(?:\/|$)")


# Attention : Certaines URL peuvent être des URL de redirection. Ainsi, la
# chaine peut être plus grande et contenir l'URL en tant que sous-chaine.
# On ne marque donc pas le début ni la fin de la chaine, et on utilise
# la fonction re.search() !

# Le "http://" ou "https://" est optionnel.


"""
Est ce que cet URL est l'URL d'une page sur Caard.co ?

@param url L'URL à examiner
@return Le nom de domaine de la page Caard.co
        Ou None si ce n'est pas une page Caard.co
"""
def validate_carrd_account_url ( url : str ) -> str :
    result = re.search( caard_account_name_regex, url )
    if result != None :
        if result.group( 1 ) != "www" :
            return result.group( 1 ) + "." + result.group( 2 )
    return None


"""
Test du bon fonctionnement de cette fonction
"""
if __name__ == '__main__' :
    test = []
    test.append( validate_carrd_account_url( "https://test27.carrd.co" ) )
    test.append( validate_carrd_account_url( "https://test27.carrd.co.another" ) )
    test.append( validate_carrd_account_url( "https://www.caard.co" ) )
    test.append( validate_carrd_account_url( "https://caard.co" ) )
    
    if test == ['test27.carrd.co', None, None, None] :
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
