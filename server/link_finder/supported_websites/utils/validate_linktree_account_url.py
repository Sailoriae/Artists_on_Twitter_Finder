#!/usr/bin/python3
# coding: utf-8

import re


# ^ = Début de la chaine, $ = Fin de la chaine
# Ne pas marquer le début ni la fin !
linktree_account_name_regex = re.compile(
    r"(?:http(?:s)?:\/\/)?(?:www\.)?linktr\.ee\/([a-zA-Z0-9_.]+)")


# Attention : Certaines URL peuvent être des URL de redirection. Ainsi, la
# chaine peut être plus grande et contenir l'URL en tant que sous-chaine.
# On ne marque donc pas le début ni la fin de la chaine, et on utilise
# la fonction re.search() !

# Le "http://" ou "https://" est optionnel.


"""
Est ce que cet URL est l'URL d'un profile Linktree ?

@param url L'URL à examiner
@return Le nom d'utilisateur du compte Linktree
        Ou None si ce n'est pas un compte Linktree
"""
def validate_linktree_account_url ( url : str ) -> str :
    # Sécurité pour sortir les sous-domaines
    if ".linktr.ee/" in url and not "www.linktr.ee/" in url :
        return None
    
    result = re.search( linktree_account_name_regex, url )
    if result != None : return result.group( 1 )
    return None


"""
Test du bon fonctionnement de cette fonction
"""
if __name__ == '__main__' :
    test = []
    test.append( validate_linktree_account_url( "https://linktr.ee/test" ) )
    test.append( validate_linktree_account_url( "https://linktr.ee/test27" ) )
    test.append( validate_linktree_account_url( "https://linktr.ee/test.._" ) )
    test.append( validate_linktree_account_url( "https://linktr.ee/" ) )
    test.append( validate_linktree_account_url( "https://linktr.ee.fr" ) )
    
    if test == ['test', 'test27', 'test.._', None, None] :
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
