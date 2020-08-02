# Artist on Twitter Finder

"Artist on Twitter Finder" est un moteur de recherche inversé d'image, spécialisé dans les illustrations postées par des artistes sur Twitter.

Contrairement aux moteurs de recherche inversé d'image généralistes, comme Google Images ou TinEye, celui-ci est très spécialisé : A partir d'une illustration postée sur un des sites supportés, il va chercher si l'artiste de cette illustration possède un compte Twitter, et, si oui, va chercher son ou ses Tweets contenant cette illustration.

Afin d'être le plus optimisé possible, ce traitement est fait par un serveur, présent dans le répertoire `server`. Ainsi, il peut indexer des comptes et leurs Tweets dans une base de données afin d'être le plus rapide possible lorsqu'il y aura une nouvelle requête pour un compte Twitter connu par le système.

Afin de recevoir des requêtes et d'y répondre, le serveur possède une API HTTP. La réponse contient l'étape du traitement de la requête, et le résultat si le traitement est terminé. La documentation de cette API est disponible dans `doc/API_HTTP.md`.


## Exemple d'utilisation

Voici un fanart de la nouvelle She-Ra, posté sur DeviantArt par DarkerEve :
https://www.deviantart.com/darkereve/art/She-Ra-The-Siege-833260345

En donnant cette URL au serveur, celui-ci va :
- Chercher si l'artiste a un ou plusieurs comptes Twitter, dans notre cas, il en a un : @DarkerEve,
- Indexer les Tweets avec un ou plusieurs images dans sa base de données,
- Chercher l'image dans l'indexation des Tweets,
- Retourner le ou les Tweets contenant l'illustration de la requête.

Dans notre exemple, le serveur a trouvé le Tweet suivant :
https://twitter.com/DarkerEve/status/1237323900410789899

Grace à l'API HTTP, envoyer une requête au serveur et recevoir sa réponse peut être fait de manière automatique. Ainsi, "Artist on Twitter Finder" peut être très intéressant pour des robots postant des illustrations sur Twitter, afin de pouvoir Retweeter l'artiste au lieu de reposter son illustration.


## Sites actuellement supportés

Lorsqu'on parle d'un "site supporté" par le serveur, on parle de l'un des sites suivants :

* DeviantArt : https://www.deviantart.com/
* Pixiv : https://www.pixiv.net/en/
* Danbooru : https://danbooru.donmai.us/ (Attention, peut contenir du NSFW directement sur la page d'acceuil)
* Derpibooru : https://derpibooru.org/
* Furbooru : https://furbooru.org/


## Répertoires

* `server` : Serveur "Artist on Twitter Finder". Pour chaque requête, trouve les comptes Twitter des artistes, indexe leurs Tweets, et recherche l'illustration de requête. Il contient une API sous la forme d'un serveur HTTP pour recevoir des requêtes et renvoyer leurs status et leurs résultats en JSON.
* `configs` : Fichier de configuration Apache2, pour faire un proxy depuis l'extérieur vers le serveur HTTP du serveur.
* `maintenance` : Scripts de maintenance de la base de données du serveur.
* `client` : Scripts du client à l'API du serveur.
* `public` : Interface web pour utiliser l'API du serveur.
* `doc` : Documentation.


## Installation et utilisation du serveur

Voir le fichier `server/README.md`.

Puis, si vous souhaitez activer l'interface web publique, consultez le fichier `configs/README.md`.


## Note de fin

Si vous souhaitez faire l'opération inverse, c'est à dire à partir d'un Tweet trouver l'image source, voici :
* SauceNAO : Un moteur de recherche inversée d'images spécialisé dans les animes, supporte Pixiv et pleins d'autres sites : https://saucenao.com/
* Twitter-SauceNAO : Un robot qui permet à partir d'un Tweet de retrouver sa source via SauceNAO.

SauceNAO est l'inverse de "Artist on Twitter Finder", car il indexe les images sur les sites sources. Ici, on indexe les images sur Twitter.
