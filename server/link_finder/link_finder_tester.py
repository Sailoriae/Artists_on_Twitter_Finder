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

test( "https://www.pixiv.net/en/artworks/82699500",
      "https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/07/02/09/32/31/82699500_p0_master1200.jpg",
      ["hongnabya"] )

test( "https://www.pixiv.net/en/artworks/82566405",
      "https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/06/26/04/01/36/82566405_p0_master1200.jpg",
      ["kazuko_art"] )

# Attention, test de NSFW
test( "https://www.pixiv.net/artworks/80875806",
      "https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/04/18/15/53/20/80875806_p0_master1200.jpg",
      ["_ssnv"] )


print( "" )
print( "TEST DE DEVIANTART :" )

test( "https://www.deviantart.com/nopeys/art/Azula-847851539",
      "Un truc qui change c'est chiant, vérifier à la main.",
      ['nopeys1'] )

# Attention, test de NSFW
test( "https://www.deviantart.com/dandonfuga/art/Harley-x-Ivy-YURI-NUDITY-warning-674880884",
      "Un truc qui change c'est chiant, vérifier à la main.",
      ['dandonfuga'] )


print( "" )
print( "TEST DE DANBOORU :" )

test( "https://danbooru.donmai.us/posts/4000914",
      "https://danbooru.donmai.us/data/139dcc6b176fb999008522b9b80a9aa8.jpg",
      ['graviqc'] )

# Attention, test de NSFW
test( "https://danbooru.donmai.us/posts/3878029",
      "https://danbooru.donmai.us/data/f316f97186dab780a2a6e54b4acccd94.png",
      ['wokada156'] )
