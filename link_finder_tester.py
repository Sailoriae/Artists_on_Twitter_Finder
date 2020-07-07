#!/usr/bin/python3
# coding: utf-8

from typing import List

from class_Link_Finder import Link_Finder


"""
Le Link Finder étant très fragile, car les API peuvent changer, voici un
script pour le tester !
"""
engine = Link_Finder()

def test ( url : str,
           should_get_image_url : str,
           should_get_twitter_accounts : List[str] ) :
    image_url = engine.get_image_url( url )
    twitter_accounts = engine.get_twitter_accounts( url )
    
    print( "" )
    print( "Test : " + url )
    
    if image_url == should_get_image_url :
        print( "Test images sources : OK !" )
        test_image_url = True
    else :
        print( "Test images sources : ECHEC !" )
        print( "On aurait dû avoir : " + should_get_image_url )
        print( "On a eu : " + image_url )
        test_image_url = False
    
    if twitter_accounts == should_get_twitter_accounts :
        print( "Test comptes Twitter : OK !" )
        test_twitter_accounts = True
    else :
        print( "Test comptes Twitter : ECHEC !" )
        print( "On aurait dû avoir : " + str(should_get_twitter_accounts) )
        print( "On a eu : " + str(twitter_accounts) )
        test_twitter_accounts = False
    
    return test_image_url and test_twitter_accounts


print( "TEST DE PIXIV :" )

test1 = test( "https://www.pixiv.net/en/artworks/82699500",
              "https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/07/02/09/32/31/82699500_p0_master1200.jpg",
              ["hongnabya"] )

test2 = test( "https://www.pixiv.net/en/artworks/82566405",
              "https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/06/26/04/01/36/82566405_p0_master1200.jpg",
              ["Kazuko_Art"] )


print( "" )
print( "TEST DE DEVIANTART :" )

test3 = test( "https://www.deviantart.com/nopeys/art/Azula-847851539",
              "Un truc qui change c'est chiant, vérifier à la main.",
              ['NOPEYS1'] )
