# Module Link Finder

Le Link Finder est l'une des deux grandes parties du serveur "Artists on Twitter Finder", avec le Tweet Finder.

La classe `Link_Finder` permet d'appeler la classe du site supporté en fonction de l'URL de requête. Les classes de chaque site supporté sont dans le module `supported_websites`.
Elle contient deux fonctions :

* `get_data( self, illust_url  : str ) -> Link_Finder_Result` :
  Prend en entrée une URL, vérifie qu'elle mène bien à un site supporté, et appel les méthodes de la classe du site supporté détecté pour remplir l'objet `Link_Finder_Result` avec les trois informations suivantes :
  - `image_urls` : Liste d'URL menant à l'image source de l'illustration (Classés de la version la plus grande à la plus petite, permet d'éviter des `PIL.Image.DecompressionBombError` durant la recherche par image),
  - `twitter_accounts` : Liste de comptes Twitter de l'artiste trouvés (Peut être vide),
  - `publish_date` : Objet `datetime` indiquant la date de publication de cette illustration.

* `link_mutiplexer ( self, url : str, source : str = "" ) -> List[str]` :
  Multiplexeur des potentiels profiles de l'artiste. Prend en entrée une URL, et retourne une liste de comptes Twitter. A sa propre liste de sites supportés. Permet d'analyser des pages Linktree par exemple, si un site supporté trouve un lien vers une profil Linktree.

Le script `link_finder_tester` permet de tester que la classe `Link_Finder` fonctionne bien.


## Attention : "URL de l'illustration"

Attention, quand on parle de l'URL de l'illustration, on parle de l'URL qui mène à une page web contenant l'illustration postée.

Exemple avec DeviantArt :
Ceci est l'URL d'une illustration postée sur ce site : `https://www.deviantart.com/darkereve/art/She-Ra-The-Siege-833260345`.
Elle mène bien à une page web contenant l'image, et non à l'image directement.

L'URL de l'illustration est l'entrée utilisateur de l'API ou de la CLI, traités dans `app.py`.

La classe `Link_Finder`, permet de savoir quel site supporté utiliser, et donc quelle classe choisir.


## Traitement d'une URL de requête dans le Link Finder

Voici les différents appels réalisés pour maximiser les chances de trouver le ou les comptes Twitter de l'artiste :

1. Méthode `get_data( URL )` : Détecte le site supporté, et appel les trois fonction du site supporté correspondant :
   * `get_image_urls( URL )` pour obtenir l'URL du fichier image,
   * `get_twitter_accounts( URL, link_mutiplexer )` pour obtenir les comptes Twitter de l'artiste, en lui passant la méthode `link_mutiplexer()`,
   * `get_datetime( URl )` pour obtenir la date de publication de l'illustration.
2. Méthode `get_twitter_accounts()` : Trouve des liens pouvant être des comptes de l'artiste sur d'autres sites (Par exemple un compte DeviantArt, Pixiv, ou Twitter). Elle passe alors ces liens à la méthode `link_mutiplexer()` qui lui a été donnée.
3. Méthode `link_mutiplexer()` (Appelée une fois par lien trouvée par l'étape précédente) : Détecte si on est capable de traiter ce lien. Si il mène un compte Twitter, elle le retourne. Si elle mène à un site connu qu'on peut analyser, elle le fait, en pouvant appeler `get_twitter_accounts( force_account )` si c'est un site supporté, en forcant le compte à analyser.
4. Méthode `get_twitter_accounts()` d'un autre site supporté : Trouve des liens menant à des comptes Twitter, et les retourne.


Ce n'est peut-être pas clair... Voici donc un exemple : **Une image sur Danbooru.**

1. Méthode `get_data( URL )` : Détecte que l'URL entrée est une image sur Danbooru, appel la méthode `get_twitter_accounts()` de son objet `Danbooru`.
2. Méthode `get_twitter_accounts()` de l'objet `Danbooru` : Trouve des liens à propos de l'artiste de l'illustration. Par exemple : Un lien vers son DeviantArt. Elle passe alors ce lien à la méthode `link_mutiplexer()`.
3. Méthode `link_mutiplexer()` : Détecte qu'un lien vers un compte DeviantArt a été donné. Elle le passe alors à la méthode `get_twitter_accounts()` de l'objet `DeviantArt` en forcant le compte DeviantArt.
4. Méthode `get_twitter_accounts()` de l'objet `DeviantArt` : Peut trouver par exemple un compte Twitter sur le profil DeviantArt de l'artiste.

Autre exemple : **Une image sur DeviantArt.**

1. Méthode `get_data( URL )` : Détecte que l'URL entrée est une image sur DeviantArt, appel la méthode `get_twitter_accounts()` de son objet `DeviantArt`.
2. Méthode `get_twitter_accounts()` de l'objet `DeviantArt` : Trouve des liens à propos de l'artiste de l'illustration. Par exemple : Un lien vers son Linktree. Elle passe alors ce lien à la méthode `link_mutiplexer()`.
3. Méthode `link_mutiplexer()` : Détecte qu'un lien vers un compte Linktree a été donné. Elle peut analyser la page pour trouver par exemple le compte Twitter de l'artiste.
