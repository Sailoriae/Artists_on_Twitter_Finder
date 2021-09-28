# Module du pipeline de traitement des requêtes de scan (Tweet Finder)

Ce sous-module du module `app` permet de traiter les requêtes d'indexation des Tweets (Ou de mise à jour de l'indexation des Tweets) de comptes Twitter.

Les requêtes sont représentées par un objet `User_Request`. L'ensemble des requêtes est géré par l'objet `User_Requests_Pipeline`, qui contient les files d'attentes. Les threads de traitement traitent ici les requêtes en paralléle ! Il n'y a donc pas vraiment de pipeline de traitement.


## Liste des procédures des threads

Ce sous-module contient les 4 threads de traitement des requêtes de scan :

- `thread_step_A_SearchAPI_list_account_tweets` : Listage des Tweets avec l'API de recherche de Twitter (Limité aux Tweets indexés dans la recherche).
- `thread_step_B_TimelineAPI_list_account_tweets` : Listage des Tweets avec l'API de timeline des comptes de Twitter (Limité aux 3 200 premiers Tweets de chaque comptes).
- `thread_step_C_index_account_tweets` : Analyse et indexation de tous les Tweets trouvés : Calcul des empreintes des images ("hash") avec le moteur CBIR, stockage dans la base de données. Ce thread traite une file d'attente commune à toutes les requêtes de scan / d'indexation.

Les deux threads de listatges peuvent travailler en paralléle sur la même requête. En effet, les threads de listage mettent les Tweets qu'ils trouvent dans une file unique à toutes les requêtes pour que les threads d'indexation les analysent et les indexent en même temps.

Avant de passer au calcul de l'empreinte, on vérifie avant que le Tweet n'est pas déjà dans la base de données.


## Procédure complémentaire

La procédure de thread `thread_retry_failed_tweets` permet de réindexer les Tweets qui ont une image mise en erreur non-insolvable par la méthode `CBIR_Engine_for_Tweets_Images.get_image_hash()` lors du passage du Tweet dans l'un des deux threads d'indexation (Voir ci-dessus).

Une erreur "non-insolvable" est une erreur qui n'est pas connue comme insolvable. Les erreurs insolvables sont directement implémentées dans le code de la fonction `get_tweet_image()`.

Ce thread peut aussi d'indexer des Tweets en connaissant uniquement leur ID. Il demande alors les détails du Tweet à l'API Twitter. Si le Tweet est introubable, il le supprime de la table des tweets à réindexer (Table `reindex_tweets`).
Ceci ne se produit pas en utilisation normale du serveur !

Ce thread force les indexation. Il efface donc tout ce qui a déjà été enregistré du Tweet (Mais uniquement si il a de nouvelles données).

Si l'indexation a réussi, le Tweet est effacé de la table `reindex_tweets`.
