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


# Faux-positifs connus (Ce ne sont pas des comptes)
# On a aussi ajouté toutes les URL qu'ils se sont réservées
# Permet de prévenir les emmerdes
FALSE_POSITIVES =  [ "posts", "policy" ]


"""
Est ce que cet URL est l'URL d'une page créateur Patreon ?

@param url L'URL à examiner
@return Le nom d'utilisateur du compte Patreon
        Ou None si ce n'est pas un compte Patreon
"""
def validate_patreon_account_url ( url : str ) -> str :
    # Sécurité pour sortir les sous-domaines
    if ".patreon.com/" in url and not "www.patreon.com/" in url :
        return None
    
    result = re.search( patreon_creator_page_regex, url )
    if result != None :
        result = result.group( 1 ) 
        if not result in FALSE_POSITIVES : return result
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
