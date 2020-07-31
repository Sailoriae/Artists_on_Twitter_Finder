#!/usr/bin/python3
# coding: utf-8

from typing import List
from datetime import datetime

from class_Link_Finder import Link_Finder


"""
Le Link Finder étant très fragile, car les API peuvent changer, voici un
script pour le tester !
"""
engine = Link_Finder()

def test ( url : str,
           should_get_image_url : str,
           should_get_twitter_accounts : List[str],
           should_get_datetime : str ) :
    data = engine.get_data( url )
    
    print( "" )
    print( "Test : " + url )
    
    if data.image_url == should_get_image_url :
        print( "Test images sources : OK !" )
        test_image_url = True
    else :
        print( "Test images sources : ECHEC !" )
        print( "On aurait dû avoir : " + should_get_image_url )
        print( "On a eu : " + data.image_url )
        test_image_url = False
    
    if data.twitter_accounts == should_get_twitter_accounts :
        print( "Test comptes Twitter : OK !" )
        test_twitter_accounts = True
    else :
        print( "Test comptes Twitter : ECHEC !" )
        print( "On aurait dû avoir : " + str(should_get_twitter_accounts) )
        print( "On a eu : " + str(data.twitter_accounts) )
        test_twitter_accounts = False
    
    if data.publish_date == should_get_datetime :
        print( "Test datetime : OK !" )
        test_datetime = True
    else :
        print( "Test datetime : ECHEC !" )
        print( "On aurait dû avoir : " + str(should_get_datetime) )
        print( "On a eu : " + str(data.publish_date) )
        test_datetime = False
    
    return test_image_url and test_twitter_accounts and test_datetime


print( "TEST DE PIXIV :" )

test( "https://www.pixiv.net/en/artworks/82699500",
      "https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/07/02/09/32/31/82699500_p0_master1200.jpg",
      ["hongnabya"],
      datetime.fromisoformat( "2020-07-02 09:32:31+09:00" ) )

test( "https://www.pixiv.net/en/artworks/82566405",
      "https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/06/26/04/01/36/82566405_p0_master1200.jpg",
      ["kazuko_art"],
      datetime.fromisoformat( "2020-06-26 04:01:36+09:00" ) )

# Attention, test de NSFW
test( "https://www.pixiv.net/artworks/80875806",
      "https://i.pximg.net/c/600x1200_90_webp/img-master/img/2020/04/18/15/53/20/80875806_p0_master1200.jpg",
      ["_ssnv"],
      datetime.fromisoformat( "2020-04-18 15:53:20+09:00" ) )


print( "" )
print( "TEST DE DEVIANTART :" )

test( "https://www.deviantart.com/nopeys/art/Azula-847851539",
      "Un truc qui change c'est chiant, vérifier à la main.",
      ['nopeys1'],
      datetime.fromisoformat( "2020-07-06 06:59:43-07:00" ) )

# Attention, test de NSFW
test( "https://www.deviantart.com/dandonfuga/art/Harley-x-Ivy-YURI-NUDITY-warning-674880884",
      "Un truc qui change c'est chiant, vérifier à la main.",
      ['dandonfuga'],
      datetime.fromisoformat( "2017-04-14 12:50:12-07:00" ) )


print( "" )
print( "TEST DE DANBOORU :" )

test( "https://danbooru.donmai.us/posts/4000914",
      "https://danbooru.donmai.us/data/139dcc6b176fb999008522b9b80a9aa8.jpg",
      ['graviqc'],
      datetime.fromisoformat( "2020-07-15 04:14:30.199000-04:00" ) )

# Attention, test de NSFW
test( "https://danbooru.donmai.us/posts/3878029",
      "https://danbooru.donmai.us/data/f316f97186dab780a2a6e54b4acccd94.png",
      ['wokada156'],
      datetime.fromisoformat( "2020-04-24 06:54:45.053000-04:00" ) )
