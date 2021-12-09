# Artists on Twitter Finder

"Artists on Twitter Finder" (AOTF) est un moteur de recherche par image (Ou "recherche inversée d'image"), spécialisé dans les illustrations postées par des artistes sur Twitter.

Contrairement aux moteurs de recherche par image généralistes, comme Google Images ou TinEye, celui-ci est très spécialisé : A partir d'une illustration postée sur un des sites supportés, il va chercher si l'artiste de cette illustration possède un compte Twitter, et, si oui, va chercher son ou ses Tweets contenant cette illustration.

Afin d'être le plus optimisé possible, ce traitement est fait par un serveur, présent dans le répertoire [`server`](server). Ainsi, il peut indexer des comptes et leurs Tweets dans une base de données afin d'être le plus rapide possible lorsqu'il y aura une nouvelle requête pour un compte Twitter connu par le système.

Afin de recevoir des requêtes et d'y répondre, le serveur possède une API HTTP. La réponse contient l'étape du traitement de la requête, et le résultat si le traitement est terminé. La documentation de cette API est disponible dans [`doc/API_HTTP.md`](doc/API_HTTP.md).

L'API HTTP peut être utilisée via une interface web, présente dans le répertoire [`public`](public). Afin qu'elle soit fonctionnelle, il faut qu'elle soit rendue accessible par un serveur HTTP, comme par exemple Apache. Ce dernier doit aussi faire un proxy vers l'API HTTP du serveur AOTF. Un exemple de configuration Apache est présent dans le répertoire [`configs`](configs).


## Exemple d'utilisation

Voici [un fanart de la nouvelle She-Ra](https://www.deviantart.com/darkereve/art/She-Ra-The-Siege-833260345), dessiné et publié sur DeviantArt par DarkerEve. En donnant cette URL au serveur AOTF, celui-ci va :
- Chercher si l'artiste a un ou plusieurs comptes Twitter, dans notre cas, il en a un : @DarkerEve,
- Indexer les Tweets avec un ou plusieurs images dans sa base de données,
- Chercher l'image dans l'indexation des Tweets,
- Retourner le ou les Tweets contenant l'illustration de la requête.

Dans notre exemple, le serveur a trouvé le Tweet [ID 1237323900410789899](https://twitter.com/DarkerEve/status/1237323900410789899).

Grace à l'API HTTP, envoyer une requête au serveur et recevoir sa réponse peut être fait de manière automatique. Ainsi, "Artists on Twitter Finder" peut être très intéressant pour des robots postant des illustrations sur Twitter, afin de pouvoir Retweeter l'artiste au lieu de reposter son illustration.


## Sites actuellement supportés

Lorsqu'on parle d'un "site supporté" par le serveur, on parle de l'un des sites suivants :

* DeviantArt : https://www.deviantart.com/
* Pixiv : https://www.pixiv.net/en/
* Danbooru : https://danbooru.donmai.us/ (Attention, peut contenir du NSFW directement sur la page d'acceuil)
* Derpibooru : https://derpibooru.org/
* Furbooru : https://furbooru.org/


## Répertoires

* [`server`](server) : Serveur "Artists on Twitter Finder". Pour chaque requête, trouve les comptes Twitter des artistes, indexe leurs Tweets, et recherche l'illustration de requête. Il contient une API sous la forme d'un serveur HTTP pour recevoir des requêtes et renvoyer leurs status et leurs résultats en JSON.
* [`configs`](configs) : Fichier de configuration Apache2, pour faire un proxy depuis l'extérieur vers le serveur HTTP du serveur.
* [`maintenance`](maintenance) : Scripts de maintenance de la base de données du serveur.
* [`client`](client) : Client à l'API du serveur, et scripts exemples.
* [`public`](public) : Interface web pour utiliser l'API du serveur.
* [`doc`](doc) : Documentation diverse. Note : Le code est bien documenté, et il y a des fichiers `README.md` dans tous les répertoires.
* [`backups`](backups) : Répertoire pour placer les Dumps de la base de données.
* [`misc`](misc) : Sauvegarde de scripts divers.


## Installation et utilisation du serveur

Voir le fichier [`server/README.md`](server/README.md).

Puis, si vous souhaitez activer l'interface web publique, consultez le fichier [`configs/README.md`](configs/README.md).


## Note de fin

Si vous souhaitez faire l'opération inverse, c'est à dire à partir d'un Tweet trouver l'image source, voici :
* [SauceNAO](https://saucenao.com/) : Un moteur de recherche inversée d'images spécialisé dans les animes, supporte Pixiv et pleins d'autres sites.
* [Twitter-SauceNAO](https://github.com/FujiMakoto/twitter-saucenao) : Un robot qui permet à partir d'un Tweet de retrouver sa source via SauceNAO.

SauceNAO est l'inverse de "Artists on Twitter Finder", car il indexe les images sur les sites sources. Ici, on indexe les images sur Twitter 
