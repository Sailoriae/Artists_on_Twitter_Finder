# Module Link Finder

Le Link Finder est l'une des deux grandes parties du serveur "Artists on Twitter Finder", avec le Tweet Finder.

La classe `Link_Finder` permet d'appeler la classe du site supporté en fonction de l'URL de requête. Les classes de chaque site supporté sont dans le module `supported_websites`.
Elle contient deux fonctions :

* `get_image_url( self, illust_url  : str ) -> str` :
  Prend en entrée une URL, vérifie qu'elle mène bien à un site supporté, appel la même fonction dans la classe du site supporte, et retourne l'URL de l'image source.
  Ou retourne `None` si l'URL passée en entrée est invalide, ou `False` si le site n'est pas supporté.

* `get_twitter_accounts( self, illust_url ) -> List[str]` :
  Prend en entrée une URL, vérifie qu'elle mène bien à un site supporté, appel la même fonction dans la classe du site supporte, et retourne la liste des comptes Twitter de l'artiste (Sans le "@") qui ont étés trouvés.
  Ou retourne `None` si l'URL passée en entrée est invalide, ou `False` si le site n'est pas supporté.

Le script `link_finder_tester` permet de tester que la classe `Link_Finder` fonctionne bien.


## Attention : "URL de l'illustration"

Attention, quand on parle de l'URL de l'illustration, on parle de l'URL qui mène à une page web contenant l'illustration postée.

Exemple avec DeviantArt :
Ceci est l'URL d'une illustration postée sur ce site : `https://www.deviantart.com/darkereve/art/She-Ra-The-Siege-833260345`.
Elle mène bien à une page web contenant l'image, et non à l'image directement.

L'URL de l'illustration est l'entrée utilisateur de l'API ou de la CLI, traités dans `app.py`.

La classe `Link_Finder`, permet de savoir quel site supporté utiliser, et donc quelle classe choisir.
