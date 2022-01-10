# Outils pour les sites supportés par le Link Finder

Ce module contient des outils pour les classes du Link Finder :

* Classe `Webpage_to_Twitter_Accounts` : Permet de scanner une page web à la recherche d'URL de comptes Twitter.

* Fonction `filter_twitter_accounts_list()` : Filtre une liste de comptes Twitter en enlevant les doublons et les comptes officiels des sites supportés.
  Utilisée uniquement par la classe `Link_Finder` afin de l'appeler qu'une seule fois.

* Fonction `get_with_rate_limits()` : Faire un GET HTTP sans se faire prendre dans des rate limits.


De plus, il contient les fonctions qui permettent de valider des URL (Avec des expressions régulières) :

* Fonction `validate_twitter_account_url()` : Vérifie qu'une URL est bien une URL d'un compte Twitter, et retourne le nom de ce compte.

* Fonction `validate_pixiv_account_url()` : Vérifie qu'une URL est bien une URL d'un compte Pixiv, et retourne l'ID de ce compte.

* Fonction `validate_deviantart_account_url()` : Vérifie qu'une URL est bien une URL d'un compte DeviantArt, et retourne le nom de ce compte (Ou "DeviantID").

* Fonction `validate_linktree_account_url()` : Vérifie qu'une URL est bien une URL d'un profile Linktree, et retourne le nom de ce profil.

* Fonction `validate_url()` : Vérifie qu'une URL est bien une URL, et retourne cette URL.

**Attention : Les validateurs de comptes ne doivent pas valider les URL des illustrations !** Par exemple, les URL d'illustrations sur DeviantArt contiennent l'URL du compte DeviantArt associé. Passer l'URL d'une illustration sur DeviantArt à la fonction `validate_deviantart_account_url` doit renvoyer `None` !
