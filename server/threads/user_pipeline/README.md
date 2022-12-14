# Pipeline de traitement des requêtes des utilisateurs

Permet de traiter les requêtes des utilisateurs.
Les requêtes sont représentées par un objet `User_Request`. L'ensemble des requêtes est géré par l'objet `User_Requests_Pipeline`, qui contient les files d'attentes.
Ces deux objets sont présents dans le répertoire [`shared_memory`](../../shared_memory).


## Liste des procédures des threads

Ce sous-module contient les 3 threads de traitement des requêtes des utilisateurs :

- `thread_step_1_link_finder` : Thread de traitement de la partie Link Finder : Vérification de l'URL d'entrée, recherche de comptes Twitter de l'artiste de l'illustration de requête, puis valide les comptes Twitter trouvés. Les comptes désactivés, suspendus, ou privés, ne sont pas validés.
- `thread_step_2_tweets_indexer` : Premier thread de traitement de la partie Tweet Finder : Lancer une requête par compte Twitter valide trouvé vers le système de traitement des requêtes se scan. Et surveille l'avancement de ce traitement.
- `thread_step_3_reverse_search` : Second thread de traitement de la partie Tweet Finder : Recherche d'image inversée.


## Notes

À tout moment, on peut connaitre le statut d'une requête via la CLI dans le processus principal, ou via l'API, gérée par le thread `http_server_thread_main`.
Lorsque la procédure est terminée, on peut aussi voir son résultat.

Lire le fichier [`API_HTTP.md`](../../../doc/API_HTTP.md) pour plus d'informations.
