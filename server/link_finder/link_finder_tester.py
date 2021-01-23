#!/usr/bin/python3
# coding: utf-8

from typing import List

# On utilise ici datetime.fromisoformat() plutpôt que dateutil.parser.isoparse()
# afin d'avoir deux libs différentes, pour être certain
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
           should_get_datetime : str,
           image_url_contains_mode : bool = False ) :
    data = engine.get_data( url )
    
    print( "" )
    print( f"Test : {url}" )
    
    if image_url_contains_mode :
        test = should_get_image_url in data.image_url
    else :
        test = data.image_url == should_get_image_url
    if test :
        print( "Test images sources : OK !" )
        test_image_url = True
    else :
        print( "Test images sources : ECHEC !" )
        print( f"On aurait dû avoir : {should_get_image_url}" )
        print( f"On a eu : {data.image_url}" )
        test_image_url = False
    
    if data.twitter_accounts == should_get_twitter_accounts :
        print( "Test comptes Twitter : OK !" )
        test_twitter_accounts = True
    else :
        print( "Test comptes Twitter : ECHEC !" )
        print( f"On aurait dû avoir : {should_get_twitter_accounts}" )
        print( f"On a eu : {data.twitter_accounts}" )
        test_twitter_accounts = False
    
    if data.publish_date == should_get_datetime :
        print( "Test datetime : OK !" )
        test_datetime = True
    else :
        print( "Test datetime : ECHEC !" )
        print( f"On aurait dû avoir : {should_get_datetime}" )
        print( f"On a eu : {data.publish_date}" )
        test_datetime = False
    
    return test_image_url and test_twitter_accounts and test_datetime


check_list = []


print( "TEST DE PIXIV :" )

check_list.append(
test( "https://www.pixiv.net/en/artworks/82699500",
      "https://i.pximg.net/img-original/img/2020/07/02/09/32/31/82699500_p0.png",
      ["hongnabya"],
      datetime.fromisoformat( "2020-07-02 09:32:31+09:00" ) ) )

check_list.append(
test( "https://www.pixiv.net/en/artworks/82566405",
      "https://i.pximg.net/img-original/img/2020/06/26/04/01/36/82566405_p0.jpg",
      ["kazuko_art"],
      datetime.fromisoformat( "2020-06-26 04:01:36+09:00" ) ) )

check_list.append(
# Attention, test de NSFW
test( "https://www.pixiv.net/artworks/80875806",
      "https://i.pximg.net/img-original/img/2020/04/18/15/53/20/80875806_p0.jpg",
      ["_ssnv"],
      datetime.fromisoformat( "2020-04-18 15:53:20+09:00" ) ) )


print( "" )
print( "TEST DE DEVIANTART :" )

check_list.append(
test( "https://www.deviantart.com/nopeys/art/Azula-847851539",
      "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/7e24a021-fa9f-40d2-b7f7-f6b9cfe1802e/de0sefn-dd065062-dd21-4dd5-a46c-402336be1a42.jpg/v1/fill/w_800,h_1237,q_75,strp/azula_by_nopeys_de0sefn-fullview.jpg?token=",
      ['nopeys1'],
      datetime.fromisoformat( "2020-07-06 06:59:43-07:00" ),
      image_url_contains_mode = True ) )

check_list.append(
test( "https://www.deviantart.com/lifeisafiction/art/Miku-Hatsune-Cosplay-844482485",
      "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/0c0cb37c-d32a-4d6e-bd8b-eca7649b1e38/ddys6ut-4baf136e-de68-4211-94c5-278176db8f25.jpg/v1/fill/w_1280,h_854,q_75,strp/miku_hatsune___cosplay_by_lifeisafiction_ddys6ut-fullview.jpg?token=",
      ['xlifeisafiction'],
      datetime.fromisoformat( "2020-06-05T10:31:38-07:00" ),
      image_url_contains_mode = True ) )

# Attention, test de NSFW
check_list.append(
test( "https://www.deviantart.com/dandonfuga/art/Harley-x-Ivy-YURI-NUDITY-warning-674880884",
      "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/6b889eb9-85d1-4954-af79-11bad3b62aec/db5t1f8-f7ef1272-a708-4750-94a9-2b2fc2ee51dc.jpg?token=",
      ['dandonfuga'],
      datetime.fromisoformat( "2017-04-14 12:50:12-07:00" ),
      image_url_contains_mode = True ) )


print( "" )
print( "TEST DE DANBOORU :" )

check_list.append(
test( "https://danbooru.donmai.us/posts/4000914",
      "https://danbooru.donmai.us/data/139dcc6b176fb999008522b9b80a9aa8.jpg",
      ['graviqc'],
      datetime.fromisoformat( "2020-07-15 04:14:30.199000-04:00" ) ) )

# Attention, test de NSFW
check_list.append(
test( "https://danbooru.donmai.us/posts/3878029",
      "https://danbooru.donmai.us/data/f316f97186dab780a2a6e54b4acccd94.png",
      ['wokada156'],
      datetime.fromisoformat( "2020-04-24 06:54:45.053000-04:00" ) ) )


print( "" )
print( "TEST DE DERPIBOORU :" )

# Test intéressant, puisque le compte Twitter de l'artiste n'est pas (encore)
# listé sur Derpibooru : https://www.derpibooru.org/tags/artist-colon-fidzfox
check_list.append(
test( "https://www.derpibooru.org/images/1851874",
      "https://derpicdn.net/img/view/2018/10/9/1851874.jpeg",
      ['fidzfox'],
      datetime.fromisoformat( "2018-10-09 01:30:23+00:00" ) ) )

# Attention, test de NSFW
check_list.append(
test( "https://www.derpibooru.org/images/2043814",
      "https://derpicdn.net/img/view/2019/5/19/2043814.png",
      ['kingkakapo'],
      datetime.fromisoformat( "2019-05-19 22:59:22+00:00" ) ) )

# Test intéressant, où il est obligé de passer dans le multiplexeur
check_list.append(
test( "https://derpibooru.org/images/2234605",
      "https://derpicdn.net/img/view/2019/12/31/2234605.png",
      ['sinrinf', 'avrameow'],
      datetime.fromisoformat( "2019-12-31 09:22:36+00:00" ) ) )

# Test intéressant, où il est obligé de passer sur la source
check_list.append(
test( "https://derpibooru.org/images/2514755",
      "https://derpicdn.net/img/view/2020/12/23/2514755.png",
      ['vadimya35764635'],
      datetime.fromisoformat( "2020-12-23 17:24:03+00:00" ) ) )


print( "" )
print( "TEST DE FURBOORU :" )

check_list.append(
test( "https://furbooru.org/images/18",
      "https://furrycdn.org/img/view/2020/4/24/18.png",
      ['twiren_arts'],
      datetime.fromisoformat( "2020-04-24 22:50:11+00:00" ) ) )


print( "" )
if all( check_list ) :
    print( "TOUS LES TESTS SONT OK !" )
else :
    print( "UN TEST A ECHOUE !" )
