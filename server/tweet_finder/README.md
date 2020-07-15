# Module Tweet Finder

Le Tweet Finder est l'une des deux grandes parties de ce projet, avec le Link Finder.

La classe `CBIR_Engine_with_Database` permet de faire :
* L'indexation des Tweets d'un compte Twitter (Seulement ceux qui n'ont pas déjà été indexés) :
  - Va chercher les Tweets d'un compte Twitter à partie du dernier scan (Ou tous les Tweet si le compte n'a pas été encore scanné) :
    - Via la librairie GetOldTweets3, module `lib_GetOldTweets3`,
    - Ou via la librairie Tweepy pour l'API Twitter publique, module `twitter`,
  - Calcul la liste des caractéristiques de toutes les images pour chaque Tweet, module `cbir_engine`,
  - Et stocke pour chaque Tweet ces listes dans la base de données, module `database`;

* Et la recherche d'un Tweet à partir d'une image, et éventuellement du compte Twitter sur lequel chercher :
  - Calcul la liste des caractéristiques de l'image de recherche, module `cbir_engine`,
  - Obtient l'itérateur sur la base de données, module `database`,
  - Calcul la distance entre l'image de requête et chaque image de l'itérateur, module `cbir_engine`,
  - Retourne le ou les Tweets correspondant.
