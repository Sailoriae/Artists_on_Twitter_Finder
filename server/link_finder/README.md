# Module Link Finder

Le Link Finder est l'une des deux grandes parties du serveur "Artists on Twitter Finder", avec le Tweet Finder.

La classe `Link_Finder` permet d'appeler la classe du site supporté en fonction de l'URL de requête. Les classes de chaque site supporté sont dans le module `supported_websites`.
Elle contient deux fonctions :

* `get_data( self, illust_url  : str ) -> Link_Finder_Result` :
  Prend en entrée une URL, vérifie qu'elle mène bien à un site supporté, et appel les méthodes de la classe du site supporté détecté pour remplir l'objet `Link_Finder_Result` avec les trois informations suivantes :
  - `image_url` : URL menant à l'image source de l'illustration,
  - `twitter_accounts` : Liste de comptes Twitter de l'artiste trouvés (Peut être vide),
  - `publish_date` : Objet `datetime` indiquant la date de publication de cette illustration.

* `link_mutiplexer ( self, url, source = "" ) -> List[str]` :
  Multiplexeur des potentiels profiles de l'artiste. Prend en entrée une URL, et retourne une liste de comptes Twitter. A sa propre liste de sites supportés. Permet d'analyser des pages Linktree par exemple, si un site supporté trouve un lien vers une profil Linktree.

Le script `link_finder_tester` permet de tester que la classe `Link_Finder` fonctionne bien.


## Attention : "URL de l'illustration"

Attention, quand on parle de l'URL de l'illustration, on parle de l'URL qui mène à une page web contenant l'illustration postée.

Exemple avec DeviantArt :
Ceci est l'URL d'une illustration postée sur ce site : `https://www.deviantart.com/darkereve/art/She-Ra-The-Siege-833260345`.
Elle mène bien à une page web contenant l'image, et non à l'image directement.

L'URL de l'illustration est l'entrée utilisateur de l'API ou de la CLI, traités dans `app.py`.

La classe `Link_Finder`, permet de savoir quel site supporté utiliser, et donc quelle classe choisir.
