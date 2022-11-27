# L'avenir d'AOTF

Dans ce document, je résume un éventuel futur problème qui mettra certainement à terme le projet Artists on Twitter Finder, ainsi que des éventuelles pistes d'améliorations.


## La menace de la fin de l'API v1.1

*Voir [`Limites_de_scan_des_comptes_Twitter.md`](Limites_de_scan_des_comptes_Twitter.md) pour les précédents problèmes de listage de comptes Twitter. Le paragraphe sur les "mixed medias" est l'origine de la réalisation du problème décrit ici, puisque je n'avais jamais touché à l'API v2 avant.*

Twitter ont prévu d'arrêter leur API v1.1. On ne sait pas quand, mais ils le feront un jour. Cependant, AOTF n'est pas passé complétement à l'API v2 à cause du Tweet Cap. En effet, pour obtenir les Tweets d'un utilisateur, AOTF utiliser ce que j'appelle l'API de timeline, qui est l'endpoint `statuses/user_timeline` sur l'API v1. Cet endpoint a déjà une limite de 100.000 requêtes par jour et par application, ce qui est embêtant pour les applications tierces comme Twidere, mais assez peu pour AOTF. Cependant, l'équivalent de cet endpoint sur l'API v2 (`/2/users/:id/tweets`) est encore plus limité, car les Tweets obtenus sont comptés dans ce qu'ils appellent le Tweet Cap, une limite mensuelle d'obtention de Tweets partagée entre plusieurs endpoints et par application, qui est par défaut de 500.000 Tweets, et peut être augmentée à 2 millions. Cette limite est juste honteuse, et détruira tout l'intérêt de l'API de Twitter, puisqu'elle ne sera plus qu'une API permettant d'obtenir des échantillons. Et le jour où l'API v1.1 fermera, Twidere n'existera plus, et AOTF aussi.


## Transformer AOTF en "Artists on Mastodon Finder"

Il pourrait être intéressant de faire un moteur de recherche par image sur Mastodon, même si finalement assez peu d'artiste y sont présents. La structure d'AOTF peut alors être réutiliser, mais beaucoup de changements sont à faire. Même chose sur Tumblr, ils ont une API publique, mais je ne connais pas ses limites.

Il faut quand même se poser la question du besoin : AOTF répond à un besoin très précis, et donc intéresse finalement très peu de personnes. Il peut être utilisé par un robot Twitter partageant des illustrations, mais il faut que son créateur soit soucieux de créditer au mieux les artistes, ce qui est très rarement le cas. Il peut aussi être utilisé par des utilisateurs qui souhaitent respecter au maximum les artistes, mais c’est encore plus rare, la plupart ne donnent même pas la source des illustrations qu’ils repostent.


## Amélioration de la recherche dans toute la base de données

*Voir [`Pistes_explorées_pour_la_recherche.md`](Pistes_explorées_pour_la_recherche.md) pour les idées originales avant qu'on ne change le moteur CBIR.*

AOTF n'a pas été conçu pour qu'on puisse rechercher dans toute sa base de données, mais seulement sur une fraction, c'est-à-dire les comptes Twitter d'un·e artiste. La recherche se fait alors par force brute, en comparant chaque empreinte des images d'un compte Twitter avec l'empreinte de l'image de requête. Ceci permet d'autoriser une légère différence dans les empreintes (6 bits maximums sur des empreintes de 64 bits), et ainsi d'éviter des faux-négatifs. Cependant, cette méthode est beaucoup trop lente pour une recherche dans toute la base de données. C'est pour cela que cette recherche dans toute la BDD se fait directement sur le serveur MySQL, en cherchant des empreintes qui correspondent exactement, et donc ne laissant aucune tolérance. Ainsi, j'ai estimé le taux de faux-négatifs à environ 10%, c'est-à-dire des résultats qui auraient dû sortir, mais qui ont été rejetés car leur empreinte a quelques bits de différence avec celle de requête.

Quitte à recréer une base de données à partir de zéro, autant en profiter pour changer la méthode d'indexation des images, et donc la méthode de recherche, dans le but d'améliorer la recherche dans toute la base de données. On pourrait utiliser un véritable moteur de recherche de plus proche voisin, mais cela nécessiterait beaucoup de ressources matérielles. Une idée que j'avais retenue dans un coin serait d'indexer une autre empreinte par image, une plus petite sur laquelle serait faite la recherche exacte, puis les résultats seraient affinés par force brute avec l'empreinte complète. Il faut juste vérifier que ces empreintes plus petites permettent plus de tolérance et donc de retourner les 10% de faux-négatifs.
