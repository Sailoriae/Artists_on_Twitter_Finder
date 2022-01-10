#!/usr/bin/python3
# coding: utf-8

from time import time, sleep


"""
Attendre précisemment jusqu'à un certain instant.

@param end_sleep_time Date de fin, instant où s'arrêter, en temps UNIX.
@param break_wait Fonction renvoyant True si il faut arrêter l'attente.

@return True si on est arrivé au bout de l'attente, False sinon.
"""
def wait_until ( end_sleep_time : float, break_wait ) -> bool :    
    # On fait des "sleep()" de 3 secondes, ce qui n'est pas précis. Cette
    # valeur est utilisée afin de savoir qu'on approche de la date de fin,
    # afin de faire une dernière attente très précise.
    almost_end_sleep_time = end_sleep_time - 3
    
    # Boucle d'attente jusqu'à la fin du temps d'attente.
    while True :
        # Vérification qu'on peut continuer.
        if break_wait() :
            return False # Terminer la fonction.
        
        # Si on est encore "loin" de la fin du temps d'attente...
        if time() < almost_end_sleep_time :
            sleep( 3 ) # Attente de 3 secondes.
            continue
        
        # Approche "finale" de la fin du temps d'attente. Il faut calculer le
        # dernier temps d'attente, et vérifier qu'il soit positif avant de le
        # passer à la fonction "sleep()".
        final_sleep = end_sleep_time - time()
        if final_sleep > 0 :
            sleep( final_sleep )
        return True # Fin de l'attente.
