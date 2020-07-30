# Module du pipeline de traitement des requêtes de scan (Tweet Finder)

Ce sous-module du module `app` permet de traiter les requêtes d'indexation des Tweets (Ou de mise à jour de l'indexation des Tweets) de comptes Twitter.

Les requêtes sont représentées par un objet `User_Request`. L'ensemble des requêtes est géré par l'objet `User_Requests_Pipeline`, qui contient les files d'attentes.


## Liste des procédures des threads

Ce sous-module contient les 3 threads de traitement des requêtes de scan :

- `thread_step_A_GOT3_list_account_tweets` : Listage des Tweets avec GetOldTweets3.
- `thread_step_B_TwitterAPI_list_account_tweets` : Listage des Tweets avec l'API publique Twitter via la librairie Tweepy.
- `thread_step_C_index_account_tweets` : Analyse et indexation des tweets trouvés par les deux threads précédents : Détection d'images, calcul de la liste des caractéristiques avec le moteur CBIR, stockage dans la base de données. Avant de passer au calcul de la liste des caractéristiques, on vérifie avant que le Tweet n'est pas déjà dans la base de données.
