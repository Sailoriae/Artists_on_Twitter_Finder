# Module des outils pour les sites supportés par le Link Finder

Ce module contient des outils pour les classes du Link Finder :

* Classe `Webpage_to_Twitter_Accounts` : Permet de scanner une page web à la recherche d'URL de comptes Twitter.

* Fonction `filter_twitter_accounts_list` : Filtre une liste de comptes Twitter en enlevant les doublons et les comptes officiels des sites supportés.
  Utilisée uniquement par la classe `Link_Finder` afin de l'appeler qu'une seule fois.

* Fonction `validate_twitter_account_url` : Vérifie qu'une URL est bien une URL d'un compte Twitter, et retourne le nom de ce compte.

* Fonction `validate_pixiv_account_url` : Vérifie qu'une URL est bien une URL d'un compte Pixiv, et retourne l'ID de ce compte.
  Utilisée par la classe `Danbooru`.

Il contient aussi des outils actuellement non-utilisés, mais conservés au cas où :

* Fonction `validate_deviantart_account_url` : Vérifie qu'une URL est bien une URL d'un compte DeviantArt, et retourne le nom de ce compte (Ou "DeviantID").
