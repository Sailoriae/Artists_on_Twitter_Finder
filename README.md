# Artists on Twitter Finder

*If you don't speak French, you can read the [English documentation](doc/English_documentation.md).*

"Artists on Twitter Finder" (AOTF) est un moteur de recherche par image (Ou "recherche inversée d'image"), spécialisé dans les illustrations postées par des artistes sur Twitter.

Contrairement aux moteurs de recherche par image généralistes, comme Google Images ou TinEye, celui-ci est très spécialisé : A partir d'une illustration postée sur un des sites supportés, il va chercher si l'artiste de cette illustration possède un compte Twitter, et, si oui, va chercher son ou ses Tweets contenant cette illustration.

Afin d'être le plus optimisé possible, ce traitement est fait par un serveur, présent dans le répertoire [`server`](server). Ainsi, il peut indexer des comptes et leurs Tweets dans une base de données afin d'être le plus rapide possible lorsqu'il y aura une nouvelle requête pour un compte Twitter connu par le système.

Afin de recevoir des requêtes et d'y répondre, le serveur possède une API HTTP. La réponse contient l'étape du traitement de la requête, et le résultat si le traitement est terminé. La documentation de cette API est disponible dans le fichier [`API_HTTP.md`](doc/API_HTTP.md).

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
* Danbooru (Site avec du contenu pour adulte)
* Derpibooru : https://derpibooru.org/
* Furbooru : https://furbooru.org/


## Répertoires

* [`server`](server) : Serveur "Artists on Twitter Finder". Pour chaque requête, trouve les comptes Twitter des artistes, indexe leurs Tweets, et recherche l'illustration de requête. Il contient une API sous la forme d'un serveur HTTP pour recevoir des requêtes et renvoyer leurs statuts et leurs résultats au format JSON.
* [`configs`](configs) : Fichier de configuration Apache2, pour faire un proxy depuis l'extérieur vers le serveur HTTP du serveur.
* [`maintenance`](maintenance) : Scripts de maintenance de la base de données du serveur.
* [`client`](client) : Client à l'API du serveur, et scripts exemples.
* [`public`](public) : Interface web pour utiliser l'API du serveur.
* [`doc`](doc) : Documentation diverse. Note : Le code est bien documenté, et il y a des fichiers `README.md` dans tous les répertoires.
* [`backups`](backups) : Répertoire pour placer les Dumps de la base de données.
* [`misc`](misc) : Sauvegarde de scripts divers.


## Utilisation d'AOTF, ou installation du serveur

**Si vous souhaitez utiliser AOTF sans l'installer :** Il faut que vous trouviez quelqu'un qui héberge une instance d'AOTF et qui la rend accessible à tout le monde. Vous pouvez alors utiliser son interface web, et son API HTTP si vous êtes développeur. Vous pouvez consulter la documentation de l'API HTTP dans le fichier [`API_HTTP.md`](doc/API_HTTP.md), ou bien directement la page de documentation sur l'interface web de l'instance.

**Si vous souhaitez installer votre instance d'AOTF :** Le fichier [`server/README.md`](server/README.md) documente l'installation et l'utilisation du serveur AOTF. Puis, si vous souhaitez activer l'interface web publique, consultez le fichier [`configs/README.md`](configs/README.md).


## Note de fin

Si vous souhaitez faire l'opération inverse, c'est à dire à partir d'un Tweet trouver l'image source, voici :
* [SauceNAO](https://saucenao.com/) : Un moteur de recherche inversée d'images spécialisé dans les animes, supporte Pixiv et pleins d'autres sites.
* [Twitter-SauceNAO](https://github.com/FujiMakoto/twitter-saucenao) : Un robot qui permet à partir d'un Tweet de retrouver sa source via SauceNAO.

SauceNAO est l'inverse de "Artists on Twitter Finder", car il indexe les images sur les sites sources. Ici, on indexe les images sur Twitter


## Licence

Copyright (C) 2020-2022 Sailoriae ([Site web](http://uneprincesse.fr), [Github](https://github.com/Sailoriae), [Twitter](https://twitter.com/Sailoriae))

Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou le modifier selon les termes de la licence publique générale GNU Affero telle que publiée par la Free Software Foundation, soit la version 3 de la licence, soit (à votre choix) toute version ultérieure.

Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS AUCUNE GARANTIE; sans même la garantie implicite de COMMERCIALISATION ou d'ADÉQUATION À UN USAGE PARTICULIER. Voir la licence publique générale GNU Affero pour plus de détails.

Vous devriez avoir reçu une copie de la licence publique générale GNU Affero avec ce programme. Si ce n'est pas le cas, consultez https://www.gnu.org/licenses/.
