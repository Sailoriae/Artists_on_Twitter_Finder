# Artist on Twitter Finder

Voici un moteur de recherche inversé d'image, spécialisé dans les illustrations postées par des artistes sur Twitter.

Contrairement aux moteurs de recherche inversé d'image généralistes, comme Google Images ou TinEye, celui-ci est très spécialisé : A partir d'une illustration postée sur un des sites supportés (DeviantArt et Pixiv pour le moment), il va chercher si l'artiste de cette illustration posède un compte Twitter, et si oui, va chercher son ou ses Tweets contenant cette illustration.

Il est composé d'un serveur, dans le répetoire `server`, et d'un client, dans le répertoire `client`. Les deux communiquent via l'API web du serveur.


## Installation du serveur

Voir `server/README.md`.
