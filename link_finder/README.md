# Module Link Finder

Ce module contient une classe par site supporté. Ces classes permettent de chercher sur ces sites les liens vers les image sources, ainsi que le ou les comptes Twitter des artistes.

Chaque classe doit contenir les deux fonctions suivantes :

* `get_image_url( self, illust_url  : str ) -> str` :
  Prend en entrée l'URL de l'illustration postée sur le site, et retourne l'URL de l'image source, ou `None` si l'URL passée en entrée est invalide.

* `get_twitter_accounts( self, illust_url ) -> List[str]` :
  Prend en entrée l'URL de l'illustration postée sur le site, et retourne la liste des comptes Twitter de l'artiste (Sans le "@") qui ont étés trouvés, ou `None` si l'URL passée en entrée est invalide.
  Doit utiliser la fonction `validate_twitter_account_url` pour reconnaitre une URL de compte Twitter et en sortir le nom de ce compte.

Ces classes peuvent contenir d'autres fonctions pour leur optimisation.


## Attention : "URL de l'illustration"

Attention, quand on parle de l'URL de l'illustration, on parle de l'URL qui mène à une page web contenant l'illustration postée.

Exemple avec DeviantArt :
Ceci est l'URL d'une illustration postée sur ce site : `https://www.deviantart.com/darkereve/art/She-Ra-The-Siege-833260345`.
Elle mène bien à une page web contenant l'image, et non à l'image directement.

L'URL de l'illustration est l'entrée utilisateur de l'API ou de la CLI, traités dans `app.py`.

La classe `Link_Finder` (Dans le répertoire parent à celui-ci), permet de savoir quel site supporté utiliser, et donc quelle classe choisir.
