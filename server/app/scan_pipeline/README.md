# Module du pipeline de traitement des requêtes de scan (Tweet Finder)

Ce sous-module du module `app` permet de traiter les requêtes d'indexation des Tweets (Ou de mise à jour de l'indexation des Tweets) de comptes Twitter.

Les requêtes sont représentées par un objet `User_Request`. L'ensemble des requêtes est géré par l'objet `User_Requests_Pipeline`, qui contient les files d'attentes.


## Liste des procédures des threads

Ce sous-module contient les 3 threads de traitement des requêtes de scan :

- `thread_step_A_GOT3_list_account_tweets` : Listage des Tweets par GetOldTweets3. L'indexation par GOT3 est séparée en deux partie car ce n'est pas un itérateur. On peut donc fare d'abord le listage des Tweets, puis leur analyse et indexation.
- `thread_step_B_GOT3_index_account_tweets` : Analyse et indexation des tweets trouvés par GetOldTweets3 : Détection d'images, calcul de la liste des caractéristiques avec le moteur CBIR, stockage dans la base de données.
- `thread_step_C_TwitterAPI_index_account_tweets` : Listage, analyse et indexation des tweets avec l'API publique de Twitter : Détection d'images, calcul de la liste des caractéristiques avec le moteur CBIR, stockage dans la base de données.

## Notes

Pour tous les threads d'indexation, avant de passer au calcul de la liste des caractéristiques, on vérifie avant que le Tweet n'est pas déjà dans la base de données.
