#!/usr/bin/python3
# coding: utf-8

import re


pixiv_account_id_regex_new = re.compile(
    r"http(?:s)?:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?users\/([0-9]+)(?:\/)?" )
pixiv_account_id_regex_old = re.compile(
    r"http(?:s)?:\/\/(?:www\.)?pixiv\.net\/member\.php\?id=([0-9]+)(?:\/)?" )

# ^ = Début de la chaine, $ = Fin de la chaine
pixiv_account_id_regex_new_strict = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?pixiv\.net\/(?:en\/)?users\/([0-9]+)(?:\/)?$" )
pixiv_account_id_regex_old_strict = re.compile(
    r"^http(?:s)?:\/\/(?:www\.)?pixiv\.net\/member\.php\?id=([0-9]+)(?:\/)?$" )

"""
Est ce que cet URL est l'URL d'un compte Pixiv ?
@param url L'URL à examiner
@param STRICT True pour que l'URL corresponde exactement
              False si l'URL peut-être contenue dans la chaine passée
              Cela peut être intéressant si on veut scanner une URL de
              redirection, contenant l'URL du compte Twitter
              (OPTIONNEL)
@return L'ID du compte Pixiv
        Ou None si ce n'est pas un compte Pixiv
"""
def validate_pixiv_account_url ( url : str, STRICT : bool = True ) -> str :
    if STRICT :
        result_new = re.match( pixiv_account_id_regex_new_strict, url )
        result_old = re.match( pixiv_account_id_regex_old_strict, url )
    else :
        result_new = re.match( pixiv_account_id_regex_new, url )
        result_old = re.match( pixiv_account_id_regex_old, url )
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
    test.append( validate_pixiv_account_url( "https://www.pixiv.net/users/24836996" ) )
    test.append( validate_pixiv_account_url( "https://www.pixiv.net/en/users/24836996" ) )
    test.append( validate_pixiv_account_url( "https://www.pixiv.net/member.php?id=24836996" ) )
    test.append( validate_pixiv_account_url( "https://pixiv.net/member.php?id=24836996/" ) )
    test.append( validate_pixiv_account_url( "https://www.pixiv.net" ) )
    
    if test == ['24836996', '24836996', '24836996', '24836996', None] :
        print( "Tests OK !" )
    else :
        print( "Tests échoués !" )
