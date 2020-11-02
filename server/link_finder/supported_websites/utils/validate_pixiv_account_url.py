#!/usr/bin/python3
# coding: utf-8

import re


# ^ = Début de la chaine, $ = Fin de la chaine
# Ne pas marquer le début ni la fin !
pixiv_account_id_regex_new = re.compile(
    r"(?:http(?:s)?:\/\/)?(?:www\.)?pixiv\.net\/(?:en\/)?users\/([0-9]+)" )
pixiv_account_id_regex_old = re.compile(
    r"(?:http(?:s)?:\/\/)?(?:www\.)?pixiv\.net\/member\.php\?id=([0-9]+)" )


# Attention : Certaines URL peuvent être des URL de redirection. Ainsi, la
# chaine peut être plus grande et contenir l'URL en tant que sous-chaine.
# On ne marque donc pas le début ni la fin de la chaine, et on utilise
# la fonction re.search() !

# Le "http://" ou "https://" est optionnel.


"""
Est ce que cet URL est l'URL d'un compte Pixiv ?

@param url L'URL à examiner
@return L'ID du compte Pixiv
        Ou None si ce n'est pas un compte Pixiv
"""
def validate_pixiv_account_url ( url : str ) -> str :
    result_new = re.search( pixiv_account_id_regex_new, url )
    result_old = re.search( pixiv_account_id_regex_old, url )
    if result_new != None : return result_new.group( 1 )
    if result_old != None : return result_old.group( 1 )
    return None


"""
Test du bon fonctionnement de cette fonction
"""
if __name__ == '__main__' :
    test = []
    test.append( validate_pixiv_account_url( "https://www.pixiv.net/users/24836996" ) )
    test.append( validate_pixiv_account_url( "https://www.pixiv.net/en/users/24836996" ) )
    test.append( validate_pixiv_account_url( "https://www.pixiv.net/member.php?id=24836996" ) )
    test.append( validate_pixiv_account_url( "https://pixiv.net/member.php?id=24836996/" ) )
    test.append( validate_pixiv_account_url( "https://www.pixiv.net" ) )
    
    if test == ['24836996', '24836996', '24836996', '24836996', None] :
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
