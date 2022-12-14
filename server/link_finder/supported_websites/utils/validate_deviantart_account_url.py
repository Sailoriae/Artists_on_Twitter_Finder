#!/usr/bin/python3
# coding: utf-8

import re


# ^ = Début de la chaine, $ = Fin de la chaine
# Ne pas marquer le début ni la fin !

# Nouveau format : deviantart.com/artiste
deviantart_account_name_regex_new = re.compile(
    r"((?:http(?:s)?:\/\/)?(?:www\.)?deviantart\.com\/([a-zA-Z0-9\-]+))" )

# Ancien format : artiste.deviantart.com
deviantart_account_name_regex_old = re.compile(
    r"((?:http(?:s)?:\/\/)?([a-zA-Z0-9\-]+)\.deviantart\.com(?:\/|$))" )


# Attention : Certaines URL peuvent être des URL de redirection. Ainsi, la
# chaine peut être plus grande et contenir l'URL en tant que sous-chaine.
# On ne marque donc pas le début ni la fin de la chaine, et on utilise
# la fonction re.search() !

# Le "http://" ou "https://" est optionnel.


# Faux-positifs connus (Ce ne sont pas des comptes)
# On a aussi ajouté toutes les URL qu'ils se sont réservées
# Permet de prévenir les emmerdes
FALSE_POSITIVES =  [ "tag", "art", "users", "search", "about", "join",
                     "submit", "core-membership", "account", "settings",
                     "chat", "groups", "shop", "forum", "notifications",
                     "watch", "daily-deviations", "topic", "popular",
                     "developers", "team" ]


"""
Est ce que cet URL est l'URL d'un compte DeviantArt ?

@param url L'URL à examiner
@return Le nom d'utilisateur du compte DeviantArt
        Ou None si ce n'est pas un compte DeviantArt
"""
def validate_deviantart_account_url ( url : str ) -> str :
    result_new = re.search( deviantart_account_name_regex_new, url )
    result_old = re.search( deviantart_account_name_regex_old, url )
    if result_new != None :
        full = result_new.group( 1 )
        result = result_new.group( 2 )
    elif result_old != None :
        full = result_old.group( 1 )
        result = result_old.group( 2 )
    else : return None
    
    if result in FALSE_POSITIVES : # Supprimer les faux-positifs connus
        return None
    if url.split(full)[-1][:5] == "/art/" : # Supprimer les pages d'illustrations
        return None
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
    test.append( validate_deviantart_account_url( "https://www.deviantart.com/mauroz/art/test" ) )
    test.append( validate_deviantart_account_url( "https://mauroz.deviantart.com/art/test" ) )
    test.append( validate_deviantart_account_url( "https://test.deviantart.com.another" ) )
    
    if test == ['mauroz', 'mauroz', 'mauroz', 'mauroz', None, None, None, None] :
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
