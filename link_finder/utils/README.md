# Module Outils pour le Link Finder

Ce module contient des outils pour les classes du Link Finder :

* Classe `Webpage_to_Twitter_Accounts` : Permet de scanner une page web à la recherche d'URL de comptes Twitter.

* Fonction `filter_twitter_accounts_list` : Filtre une liste de comptes Twitter en enlevant les doublons et les comptes officiels des sites supportés.

* Fonction `validate_twitter_account_url` : Vérifie qu'une URL est bien une URL d'un compte Twitter, et retourne le nom de ce compte.


Il contient aussi des outils non-utilisés dans ce projet, mais conservés au cas où :

* Fonction `validate_deviantart_account_url` : Vérifie qu'une URL est bien une URL d'un compte DeviantArt, et retourne le nom de ce compte (Ou "DeviantID").

* Fonction `validate_pixiv_account_url` : Vérifie qu'une URL est bien une URL d'un compte Pixiv, et retourne l'ID de ce compte.
