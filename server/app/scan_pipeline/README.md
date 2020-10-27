# Module du pipeline de traitement des requêtes de scan (Tweet Finder)

Ce sous-module du module `app` permet de traiter les requêtes d'indexation des Tweets (Ou de mise à jour de l'indexation des Tweets) de comptes Twitter.

Les requêtes sont représentées par un objet `User_Request`. L'ensemble des requêtes est géré par l'objet `User_Requests_Pipeline`, qui contient les files d'attentes. Les threads de traitement traitent ici les requêtes en paralléle ! Il n'y a donc pas vraiment de pipeline de traitement.


## Liste des procédures des threads

Ce sous-module contient les 4 threads de traitement des requêtes de scan :

- `thread_step_A_SearchAPI_list_account_tweets` : Listage des Tweets avec l'API de recherche de Twitter (Limité aux Tweets indexés dans la recherche).
- `thread_step_B_TimelineAPI_list_account_tweets` : Listage des Tweets avec l'API de timeline des comptes de Twitter (Limité aux 3 200 premiers Tweets de chaque comptes).
- `thread_step_C_SearchAPI_index_account_tweets` : Analyse et indexation des tweets trouvés avec l'API de recherche : Calcul de la liste des caractéristiques avec le moteur CBIR, stockage dans la base de données.
- `thread_step_D_TimelineAPI_index_account_tweets` : Analyse et indexation des tweets trouvés avec l'API de timeline : Calcul de la liste des caractéristiques avec le moteur CBIR, stockage dans la base de données.

Ces 4 threads peuvent travailler en paralléle sur la même requête. En effet, la requête contient deux files, une pour les Tweets trouvés avec l'API de recherche et une pour ceux trouvés avec l'API de timeline. Les threads de listage mettent les Tweets qu'ils trouvent dans l'une des deux files, pour que les threads d'indexation les analysent et les indexent en même temps.

Avant de passer au calcul de la liste des caractéristiques, on vérifie avant que le Tweet n'est pas déjà dans la base de données.
