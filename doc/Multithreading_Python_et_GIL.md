# Multithreading en Python et GIL

Ce projet est très multi-threadé, ce qui permet de traiter plusieurs requêtes en même temps, et d'accélérer leur temps de traitement.

Sauf que, quand j'ai conçu ce système, il y a quelque chose que je ne connaissais pas : Le GIL.

Le Global Interpreter Lock, ou "GIL", est une sorte de sémaphore qui empêche deux threads Python de s'éxécuter en même temps, afin de ne pas corrompre la mémoire. Ainsi, le multi-threading en Python (Module `threading`) n'est pas du vrai multi-threading, car les instructions Python ne sont pas exécutées en même temps. Si l'on veut faire du vrai multi-threading en Python, il faut faire du multi-processing (Module `multiprocessing`).

Et faire du multi-processing Python casse complétement la mémoire partagée de ce projet (Classe `Shared_Memory` et ses sous-objets). Pour partager des données, il faut obligatoirement faire un serveur de mémoire partagée.

Ainsi, j'ai exploré deux solutions de serveur de mémoire partagée :

- Les "Managers" du module `multiprocessing`. Leur gros problème est qu'ils n'acceptent qu'une liste restreinte d'objets, ce qui transforme complétement la mémoire partagée et leur utilisation.

- La librarie `Pyro4`. Peut supporter des classes, et exécuter coté-serveur le code de leurs attributs, mais pas pour les sous-objets ! La classe `Shared_Memory` devient alors une grande classe de plus de 500 lignes !

Je suis allé beaucoup plus loin avec `Pyro4` que `multiprocessing`, car son utilisation est plus simple et plus adaptée, alors que `multiprocessing` est très fragile, et sa documentation peu précise.

Sauf qu'un grand principe se perd : Les requêtes dans la liste des requêtes sont les mêmes que dans les threads et les files d'attentes, car les objets Python sont passés par adresse ! Il faut alors revoir toute la gestion des requêtes.

Ainsi, l'implémentation d'un vrai multi-threading nécéssite une réécriture quasi-complète du module `app`.
