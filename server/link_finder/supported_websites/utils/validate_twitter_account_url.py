#!/usr/bin/python3
# coding: utf-8

import re

# ^ = Début de la chaine, $ = Fin de la chaine
# Ne pas marquer le début ni la fin !
twitter_account_name_regex = re.compile(
    r"(?:http(?:s)?:\/\/)?(?:www\.|mobile\.)?twitter\.com\/(?:#!\/)?(?:@)?([a-zA-Z0-9_]+)" )


# Attention : Certaines URL peuvent être des URL de redirection. Ainsi, la
# chaine peut être plus grande et contenir l'URL en tant que sous-chaine.
# On ne marque donc pas le début ni la fin de la chaine, et on utilise
# la fonction re.search() !

# Le "http://" ou "https://" est optionnel.


"""
Est ce que cet URL est l'URL d'un compte Twitter ?

@param url L'URL à examiner
@return Le nom d'utilisateur du compte Twitter
        Ou None si ce n'est pas un compte Twitter
"""
def validate_twitter_account_url ( url : str ) -> str :
    result = re.search( twitter_account_name_regex, url )
    if result != None : result = result.group( 1 )
    else : return None
    
    if result in [ "intent" ] : # Supprimer les faux-positifs connus
        return None
    else :
        return result


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
