# Module du serveur de mémoire partagée (Dépendance de `app.py`)

La mémoire partagée consiste en un serveur tournant avec la librairie Pytho `Pyro4`.

Documentation : https://pyro4.readthedocs.io/en/stable/index.html

Cette librairie permet de partager des objets entre des processus (Car nous sommes obligés de faire du multi-processus et non du multi-threading à cause du GIL). De plus, elle permet aussi de faire des systèmes distribués. "Artists on Twitter Finder" peut donc être distribué sur plusieurs serveurs (En modifiant un peu le code).


## Origine de ce module

Le Global Interpreter Lock, ou "GIL", est une sorte de sémaphore qui empêche deux threads Python de s'éxécuter en même temps, afin de ne pas corrompre la mémoire. Ainsi, le multi-threading en Python (Module `threading`) n'est pas du vrai multi-threading, car les instructions Python ne sont pas exécutées en même temps. Si l'on veut faire du vrai multi-threading en Python, il faut faire du multi-processing (Module `multiprocessing`).

Et faire du multi-processing Python rend l'utilisation d'une mémoire partagée impossible ! Pour partager des données, il faut obligatoirement faire un serveur de mémoire partagée.

Ainsi, j'ai exploré deux solutions de serveur de mémoire partagée :
- Les "Managers" du module `multiprocessing`. Leur gros problème est qu'ils n'acceptent qu'une liste restreinte d'objets, ce qui transforme complétement la mémoire partagée et leur utilisation.

- La librarie `Pyro4`. Peut supporter des classes, et exécuter coté-serveur le code de leurs attributs, mais pas pour les sous-objets ! Cependant, une parade a été trouvée pour pallier ce problème, et faire une mémoire partagée efficace, voir ci-dessous.


## Procédure de lancement : `thread_pyro_server`

Cette procédure est appelée en procédure de création d'un processus (Ou d'un thread) par `app.py`.
Le script `thread_pyro_server.py` peut être éxécuté indépendamment... Mais ça ne sert à rien, sauf à débugger.

Code pour accéder à la mémoire partagée (Depuis IPython par exemple) et l'explorer pour débugger :
```
import Pyro4
Pyro4.config.SERIALIZER = "pickle"

e = Pyro4.Proxy( "PYRO:shared_memory@localhost:3300" )
```


## Objets dans la mémoire partagée

L'objet racine de la mémoire partagée est `Shared_Memory`. Lors qu'un objet est créé, sa méthode `register_obj` est appelée afin d'enregistrer le nouvel objet sur le serveur Pyro. Cela permet de faire des "pseudos-sous-objets".

En effet, Pyro permet d'éxécuter les méthodes des objets sur le serveur, mais pas des sous-objets ! Afin de pallier à ce problème (Et afin d'utiliser des Sémphores, qui se sont pas tranférables car non-sérialisables), on enregistre les URI des enregistrement des objets, et non les objets eux-mêmes. Ainsi, lorsqu'un getter est appelé, il renvoit un objet `Pyro4.Proxy` qui est connecté au sous-objet.

Ainsi, l'utilisation est transparente dans le module `app` !

Ainsi, toutes les méthodes de tous les objets présents dans ce module sont exécutées coté serveur Pyro !

Arbre des objets :
- `Shared_Memory` : Objet racine.

  - Attribut `user_requests` : URI vers objet `User_Requests_Pipeline` : Mémoire partagée pour les threads de traitement des requêtes des utilisateurs.
    - Liste `requests` (Privé) : Liste d'URI vers objets `User_Request` : Requêtes des utilisateuts.
    - Attribut `requests_sem` (Privé) : URI vers objet `Pyro_Semaphore` : Vérrouillage de la liste précédente.
    - Attributs `*_queue` : URIs vers objets `Pyro_Queue` : Files d'attente des différentes threads de traitement. Peuvent contenir des URI de la liste `requests`.
    - Attribut `limit_per_ip_addresses` : URI vers objet `HTTP_Requests_Limitator` : Limitateur du nombre de requêtes en cours de traitement par adresse IP.
    - Attribut `requests_in_thread` : URI vers objet `Threads_Register` : Objet auquel les threads de traitement déclarent les requêtes qu'ils sont en train de traiter (En donnent l'URI de la requête concernée).
    - Attribut `thread_step_2_tweets_indexer_sem` : URI vers objet `Pyro_Semaphore` : Verouillage du lancement d'une nouvelle requête de scan dans l'étape de traitement utilisateur numéro 2.

  - Attribut `scan_requests` : URI vers objet `Scan_Requests_Pipeline` : Mémoire partagée pour les threads de traitement des requêtes de scan.
    - Liste `requests` (Privé) : Liste d'URI vers objets `Scan_Request` : Requêtes des utilisateuts.
      - Attribut `GetOldTweets3_tweets_queue` (Privé) : URIs vers objet `Pyro_Queue` : File d'attente des Tweets trouvés par GOT3.
      - Attribut `TwitterAPI_tweets_queue` : URIs vers objet `Pyro_Queue` : File d'attente d'attente des Tweets trouvés par l'API Twitter.
    - Attribut `requests_sem` (Privé) : URI vers objet `Pyro_Semaphore` : Vérrouillage de la liste précédente.
    - Attributs `*_queue` : URIs vers objets `Pyro_Queue` : Files d'attente des différentes threads de traitement. Peuvent contenir des URI de la liste `requests`.
    - Attribut `requests_in_thread` : URI vers objet `Threads_Register` : Objet auquel les threads de traitement déclarent les requêtes qu'ils sont en train de traiter (En donnent l'URI de la requête concernée).

  - Attribut `http_limitator` : URI vers objet `HTTP_Requests_Limitator` : Limitateur du nombre de requêtes sur l'API HTTP.

Voir chaque classe pour plus de documentation.


# Notes

Les objets `Pyro4.Proxy` ferment leur connexion lorsqu'ils arrivent dans le garbadge collector. Source : https://github.com/irmen/Pyro4/blob/79de6434259ff82d202090cbd0901673d4b8344b/src/Pyro4/core.py#L264

