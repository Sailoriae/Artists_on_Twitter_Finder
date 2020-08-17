# Module du pipeline de traitement des requêtes des utilisateurs

Ce sous-module du module `app` permet de traiter les requêtes des utilisateurs.

Les requêtes sont représentées par un objet `Scan_Request`. L'ensemble des requêtes est géré par l'objet `Scan_Requests_Pipeline`, qui contient les files d'attentes.


## Liste des procédures des threads

Ce sous-module contient les 4 threads de traitement des requêtes des utilisateurs :

- `thread_step_1_link_finder` : Thread de traitement de la partie Link Finder : Vérification de l'URL d'entrée, reherche de comptes Twitter de l'artiste de l'illustration de requête, puis valide les comptes Twitter trouvés. Les comptes désactivés, suspendus, ou privés, ne sont pas validés.
- `thread_step_2_tweets_indexer` : Premier thread de traitement de la partie Tweet Finder : Lancer une requête par compte Twitter valide trouvé vers le système de traitement des requêtes se scan. Et surveille l'avancement de ce traitement.
- `thread_step_3_reverse_search` : Second thread de traitement de la partie Tweet Finder : Recherche d'image inversée.
- `thread_step_4_filter_results` : Un peu comme un troisième thread de la partie Tweet Finder : Filtrage des résultats de la recherche inversée, car à cause de la compression des image sur les serveurs de Twitter, il peut y avoir des faux positifs.


## Notes

A tout moment, on peut connaitre le status d'une requête via la CLI dans le processus principal, ou via l'API, gérée par le thread `http_server_thread_main`.
Lorsque la procédure est terminée, on peut aussi voir son résultat.

Voir `doc/API_HTTP.md` pour plus d'informations.
