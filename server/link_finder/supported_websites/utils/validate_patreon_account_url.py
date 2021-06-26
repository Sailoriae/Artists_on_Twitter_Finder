#!/usr/bin/python3
# coding: utf-8

import re


# ^ = Début de la chaine, $ = Fin de la chaine
# Ne pas marquer le début ni la fin !
patreon_creator_page_regex = re.compile(
    r"(?:http(?:s)?:\/\/)?(?:www\.)?patreon\.com\/([a-zA-Z0-9]+)")


# Attention : Certaines URL peuvent être des URL de redirection. Ainsi, la
# chaine peut être plus grande et contenir l'URL en tant que sous-chaine.
# On ne marque donc pas le début ni la fin de la chaine, et on utilise
# la fonction re.search() !

# Le "http://" ou "https://" est optionnel.


"""
Est ce que cet URL est l'URL d'une page créateur Patreon ?

@param url L'URL à examiner
@return Le nom d'utilisateur du compte Patreon
        Ou None si ce n'est pas un compte Patreon
"""
def validate_patreon_account_url ( url : str ) -> str :
    result = re.search( patreon_creator_page_regex, url )
    if result != None : return result.group( 1 )
    return None


"""
Test du bon fonctionnement de cette fonction
"""
if __name__ == '__main__' :
    test = []
    test.append( validate_patreon_account_url( "https://www.patreon.com/erb" ) )
    test.append( validate_patreon_account_url( "https://patreon.com/erb" ) )
    test.append( validate_patreon_account_url( "https://patreon.com/" ) )
    test.append( validate_patreon_account_url( "https://www.patreon.com.fr/erb" ) )
    
    if test == ['erb', 'erb', None, None] :
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )