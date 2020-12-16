#!/usr/bin/python3
# coding: utf-8

from time import time, sleep


"""
J'ai créé cette fonction afin d'étaler les MàJ auto et les reset de curseurs
sur leur période respective.
L'avantage est que cela répartit la charge du serveur du serveur, évitant des
pics avec pleins de MàJ en même temps.

Cependant, ce système a un gros point faible : Il ne faut jamais que le
serveur s'arrête !
Sinon, un retard se crée forcément, et n'est rattrapé qu'à la fin de la période
de mise à jour.

Second problème : Avec une BDD "légère" (Peu de comptes), le temps entre chaque
lancement de l'action peut être très grand. Comme le temps d'attente est avant
l'action (Impossible d'inverser), il risque de n'y avoir aucune MàJ si le
serveur est souvent éteint.

Bref, globalement, c'est pas une bonne idée du tout !

Meilleure idée : Limiter les temps d'attente à une valeur maximale, cette
valeur étant le nombre d'éléments divisé par la période.
"""


"""
Répartiteur d'appels périodiques à une fonction sur une intervalle de temps.

@param get_count Fonction donnant le nombre d'actions à faire.
@param period En secondes, la période où faire les actions.
@param do_action Fonction à appeler pour réaliser l'action.
@param keep_alive Fonction renvoyant False si on doit s'arrêter.
@param break_wait Fonction renvoyant True si il faut arrêter une attente et
                  lancer directement l'action.
"""
def action_dispatcher( get_count, period, do_action, keep_alive, break_wait = None ) :
    # La variable "start" contient l'instant où on exécute une action. Cela
    # permet de savoir précisemment quand il faudra exécuter la suivante, en
    # prenant en compte le temps d'appel à "do_action".
    start = time() # En secondes.
    
    # Pas d'appel à "keep_alive" pour le "while", serait inutile.
    while True :
        # Variable pour annuler l'appel à "do_action" pour cette itération.
        cancel_action = False
        
        # On calcul à chaque itération le temps d'attente entre chaque action,
        # afin qu'il soit dynamiquement mis à jour en cas de changement du
        # nombre d'actions à faire.
        try :
            wait_time = period / get_count() # En secondes.
        
        # Si il n'y a aucune action à faire ("get_count" renvoi 0), on dors
        # 1 heure, donc 3600 secondes.
        except ZeroDivisionError :
            wait_time = 3600
            cancel_action = True
        
        # Calculer la fin précise du temps d'attente, par rapport à la dernière
        # exécution de l'action.
        end_sleep_time = start + wait_time
        
        # On fait des attentes de 3 secondes, ce qui n'est pas précis. Cette
        # valeur est utilisée afin de savoir qu'on approche de la date de fin,
        # afin de faire une dernière attente très précise.
        almost_end_sleep_time = end_sleep_time - 3
        
        # Boucle d'attente jusqu'à la prochaine éxécution de l'action.
        while True :
            # Vérification qu'on peut continuer.
            if not keep_alive() :
                return # Terminer la fonction.
            
            # Vérification qu'on ne doit pas lancer l'action maintenant.
            if break_wait() :
                break
            
            # Si on est encore "loin" de la fin du temps d'attente...
            if time() < almost_end_sleep_time :
                sleep( 3 ) # Attente de 3 secondes.
                continue
            
            # Approche "finale" de l'instant où exécuter l'action. Il faut
            # calculer le dernier temps d'attente, et vérifier qu'il soit
            # positif avant de le passer à la fonction "sleep()".
            final_sleep = end_sleep_time - time()
            if final_sleep > 0 :
                sleep( final_sleep )
            break # Fin de l'attente jusqu'à la prochaine éxécution de l'action.
        
        # On met à jour la variable "start" avant de faire l'action. Ainsi, le
        # temps d'éxécution de l'action sera enlevé de la prochaine attente.
        start = time()
        
        # Réaliser l'action, c'est à dire appeler la fonction passée en param.
        if not cancel_action :
            do_action()
