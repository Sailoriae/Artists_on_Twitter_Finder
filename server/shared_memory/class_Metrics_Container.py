#!/usr/bin/python3
# coding: utf-8

import Pyro4
from statistics import mean


"""
Conteneur des mesures des temps d'exécutions.
"""
@Pyro4.expose
class Metrics_Container :
    def __init__ ( self ) :
        # Classe Tweets_Lister_with_SearchAPI
        self._step_A_times = []
        
        # Classe Tweets_Lister_with_TimelineAPI
        self._step_B_times = []
        
        # Classe Tweets_Indexer pour l'étape C
        self._step_C_times = []
        self._step_C_calculate_features_times = []
        self._step_C_insert_into_times = []
        
        # Classe Tweets_Indexer pour l'étape D
        self._step_D_times = []
        self._step_D_calculate_features_times = []
        self._step_D_insert_into_times = []
        
        # Execution complète du Link Finder
        self._step_1_times = []
        
        # Classe Image_Features_Iterator
        self._step_3_times = []
        self._step_3_iteration_times = []
        self._step_3_usage_times = []
        
        # Fonction thread_step_4_filter_results
        self._step_4_times = []
        
        # Temps de traitement complet
        self._user_request_full_time = []
        self._scan_request_full_time = []
    
    """
    @param step_A_time Temps d'éxécution MOYEN pour le listage des Tweets avec
                       la librairie SearchAPI.
    """
    def add_step_A_time ( self, step_A_time ) :
        self._step_A_times.append( step_A_time )
    
    """
    @param step_B_time Temps d'éxécution MOYEN pour le listage des Tweets avec
                       l'API Twitter publique.
    """
    def add_step_B_time ( self, step_A_time ) :
        self._step_B_times.append( step_A_time )
    
    """
    @param step_C_times Liste de temps d'éxécution pour indexer un Tweet.
    @param step_C_calculate_features_times Liste des temps d'éxécution pour
                                           calculer les caractéristiques des
                                           images d'un Tweet.
    @param step_C_insert_into_times Liste des temps d'éxécution pour insérer
                                    un Tweet dans la BDD.
    """
    def add_step_C_times ( self, step_C_times, step_C_calculate_features_times, step_C_insert_into_times ) :
        self._step_C_times += step_C_times
        self._step_C_calculate_features_times += step_C_calculate_features_times
        self._step_C_insert_into_times += step_C_insert_into_times
    
    """
    @param step_D_times Liste de temps d'éxécution pour indexer un Tweet.
    @param step_D_calculate_features_times Liste des temps d'éxécution pour
                                           calculer les caractéristiques des
                                           images d'un Tweet.
    @param step_D_insert_into_times Liste des temps d'éxécution pour insérer
                                    un Tweet dans la BDD.
    """
    def add_step_D_times ( self, step_D_times, step_D_calculate_features_times, step_D_insert_into_times ) :
        self._step_D_times += step_D_times
        self._step_D_calculate_features_times += step_D_calculate_features_times
        self._step_D_insert_into_times += step_D_insert_into_times
    
    """
    @param step_1_times Temps d'éxécution global à l'étape 1.
    """
    def add_step_1_times ( self, step_1_times : float ) :
        self._step_1_times.append( step_1_times )
    
    """
    @param step_3_times Temps d'éxécution pour faire la recherche inversée.
    @param step_3_iteration_times Liste des temps d'éxécution pour itérer sur
                                  la base de données.
    @param step_3_usage_times Liste des temps d'éxécution de l'utilisation.
    """
    def add_step_3_times ( self, step_3_times, step_3_iteration_times, step_3_usage_times ) :
        self._step_3_times.append( step_3_times )
        self._step_3_iteration_times += step_3_iteration_times
        self._step_3_usage_times += step_3_usage_times
    
    """
    @param step_4_times Temps d'éxécution pour filtrer la liste des résultats.
    """
    def add_step_4_times ( self, step_4_times : float ) :
        self._step_4_times.append( step_4_times )
    
    """
    Enregistrer le temps de traitement complet d'une requête utilisateur.
    @param scan_request_full_time Temps d'éxécution.
    """
    def add_user_request_full_time ( self, user_request_full_time : float ) :
        self._user_request_full_time.append( user_request_full_time )
    
    """
    Enregistrer le temps de traitement complet d'une requête de scan.
    @param scan_request_full_time Temps d'éxécution.
    """
    def add_scan_request_full_time ( self, scan_request_full_time : float ) :
        self._scan_request_full_time.append( scan_request_full_time )
    
    """
    @return Une chaine de caractères à afficher.
    """
    def get_metrics ( self ) :
        to_print = ""
        if self._step_A_times != [] :
            to_print += f"Etape A : Temps moyen pour lister avec SearchAPI : {mean(self._step_A_times)} ({len(self._step_A_times)} listages)\n"
        if self._step_B_times != [] :
            to_print += f"Etape B : Temps moyen pour lister avec TimelineAPI : {mean(self._step_B_times)} ({len(self._step_B_times)} listages)\n"
        if self._step_C_times != [] :
            to_print += f"Etape C : Temps moyen pour indexer avec SearchAPI : {mean(self._step_C_times)} ({len(self._step_C_times)} tweets)\n"
        if self._step_C_calculate_features_times != [] :
            to_print += f" - Dont : Calcul CBIR d'un Tweet : {mean(self._step_C_calculate_features_times)} ({len(self._step_C_calculate_features_times)} tweets)\n"
        if self._step_C_insert_into_times != [] :
            to_print += f" - Dont : INSERT INTO d'un Tweet : {mean(self._step_C_insert_into_times)} ({len(self._step_C_insert_into_times)} tweets)\n"
        if self._step_D_times != [] :
            to_print += f"Etape D : Temps moyen pour indexer avec TimelineAPI : {mean(self._step_D_times)} ({len(self._step_D_times)} tweets)\n"
        if self._step_D_calculate_features_times != [] :
            to_print += f" - Dont : Calcul CBIR d'un Tweet : {mean(self._step_D_calculate_features_times)} ({len(self._step_D_calculate_features_times)} tweets)\n"
        if self._step_D_insert_into_times != [] :
            to_print += f" - Dont : INSERT INTO d'un Tweet : {mean(self._step_D_insert_into_times)} ({len(self._step_D_insert_into_times)} tweets)\n"
        if self._step_1_times != [] :
            to_print += f"Etape 1 : Temps moyen pour passer dans le Link Finder : {mean(self._step_1_times)} ({len(self._step_1_times)} éxécutions)\n"
        if self._step_3_times != [] :
            to_print += f"Etape 3 : Temps moyen pour éxécuter la recherche inversée : {mean(self._step_3_times)} ({len(self._step_3_times)} recherches de {int(len(self._step_3_usage_times)/len(self._step_3_times))} comparaisons en moyenne)\n"
        if self._step_3_iteration_times != [] :
            to_print += f" - Dont : Itérer sur la base de données : {mean(self._step_3_iteration_times)} ({len(self._step_3_iteration_times)} itérations)\n"
        if self._step_3_usage_times != [] :
            to_print += f" - Dont : Comparer deux vecteurs : {mean(self._step_3_usage_times)} ({len(self._step_3_usage_times)} images)\n"
        if self._step_4_times != [] :
            to_print += f"Etape 4 : Temps moyen pour filtrer la liste des résultats : {mean(self._step_4_times)} ({len(self._step_4_times)} filtrages)\n"
        if self._user_request_full_time != [] :
            to_print += f"Temps moyen pour traiter une requête utilisateur : {mean(self._user_request_full_time)} ({len(self._user_request_full_time)} requêtes)\n"
        if self._scan_request_full_time != [] :
            to_print += f"Temps moyen pour traiter une requête de scan : {mean(self._scan_request_full_time)} ({len(self._scan_request_full_time)} requêtes)\n"
        if to_print == "" :
            to_print = "Aucune statistique disponible ! Aucune requête n'a été lancée, ou le paramètre \"ENABLE_METRICS\" est à \"False\"."
        return to_print
