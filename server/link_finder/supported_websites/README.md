# Sites supportés par le Link Finder

Ce module contient une classe par site supporté. Ces classes permettent de chercher sur ces sites les liens vers les images sources, ainsi que le ou les comptes Twitter des artistes.

Chaque classe doit contenir les deux fonctions suivantes :

* `get_image_urls( self, illust_url  : str ) -> List[str]` :
  Prend en entrée l'URL de l'illustration postée sur le site, et retourne une liste d'URL de l'image source (La première doit être celle avec la meilleure résolution et qualité, les suivantes doivent être plus légères), ou `None` si l'URL passée en entrée est invalide.
  **Doit retourner les images en qualité maximale !** Déjà que Twitter compresse, on ne va pas écarter encore plus les images avec d'autres compression.

* `get_twitter_accounts( self, illust_url ) -> List[str]` :
  Prend en entrée l'URL de l'illustration postée sur le site, et retourne la liste des comptes Twitter de l'artiste (Sans le "@") qui ont étés trouvés, ou `None` si l'URL passée en entrée est invalide.
  Doit utiliser la fonction `validate_twitter_account_url()` pour reconnaitre une URL de compte Twitter et en sortir le nom de ce compte.
  - Peut aussi prendre un paramètre optionnel `multiplexer` dans lequel la classe `Link_Finder` donne sa méthode `link_mutiplexer()` (Multiplexeur de liens). Appeler ensuite cette méthode pour toutes les URL pouvant mener à des profils de l'artiste sur d'autres sites. Voir sa documentation pour plus d'informations.
  - Peut aussi prendre un paramètre optionnel utilisé par le multiplexeur de liens pour forcer le scan de la page d'un artiste. **Attention :** Si ce paramètre et `multiplexer` sont spécifiables, cette méthode **ne doit surtout pas aller scanner la page de l'artiste d'elle-même**. Elle doit passer par le multiplexeur de liens. Cela permet d'empêcher de scanner deux fois la page de l'artiste.

* `get_datetime ( self, illust_url  : str ) -> str` :
  Prend en entrée l'URL de l'illustration postée sur le site, et retourne l'objet `datetime` indiquant la date de publication de cette illustration, ou `None` si l'URL passée en entrée est invalide.

Ces classes peuvent contenir d'autres fonctions pour leur optimisation.


## Ajouter un site supporté

**Un site supporté doit être un site sur lequel on peut trouver des illustrations, associées aux comptes Twitter des artistes.** Ainsi, les site sur lesquels les artistes publient eux-mêmes leurs illustrations, comme par exemple DeviantArt ou Pixiv, peuvent être des site supportés par AOTF. Les sites de republications, comme les boorus et les imageboards, peuvent aussi être supporté à la condition qu'ils fassent l'effort de lister les comptes des artistes, notamment leurs comptes Twitter. Danbooru le fait très bien, Derpibooru plutôt bien, et Furbooru pas trop mal. D'autres boorus comme par exemple SankakuComplex, Gelbooru, Rule34 ou E621, ne le font pas du tout, et par conséquent ne peuvent pas être des sites supportés par AOTF. En effet, comme ces boorus ne lient que la source des illustrations, ils sont inutiles pour chercher les comptes Twitter des artistes (Et si la source est un Tweet, AOTF ne sert alors à rien).

Conséquemment à cette règle :
* AOTF devrait supporter plus de sites sur lesquels les artistes publient eux-mêmes leurs illustrations, comme par exemple ArtStation, FurAffinity, ou InkBunny.
* AOTF pourrait supporter "à moitié" les boorus cités ci-dessus, c'est à dire qu'il irait juste explorer la source des illustrations. Ils ne seraient alors par listés comme des sites supportés. C'est ce qu'on fait déjà avec Linktree et Patreon (Voir la méthode `Link_Finder._link_mutiplexer()`).

Une fois un site supporté ajouté, il faut mettre à jour la liste des sites supportés dans le [`README.md`](../../../README.md) racine, ainsi que les fichiers HTML de l'interface web (Répertoire [`public`](../../../public)) pour indiquer que ce site est supporté.
