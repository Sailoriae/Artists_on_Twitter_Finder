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
        # Classe Tweets_Lister_with_GetOldTweets3
        self._step_A_times = []
        
        # Classe Tweets_Lister_with_TwitterAPI
        self._step_B_times = []
        
        # Classe Tweets_Indexer_with_GetOldTweets3
        self._step_C_times = []
        self._step_C_calculate_features_times = []
        self._step_C_insert_into_times = []
        
        # Classe Tweets_Indexer_with_TwitterAPI
        self._step_D_times = []
        
        # Classe Image_Features_Iterator
        self._step_3_iteration_times = []
        self._step_3_usage_times = []
    
    """
    @param step_A_time Temps d'éxécution MOYEN pour le listage des Tweets avec
                       la librairie GetOldTweets3.
    """
    def add_step_A_time ( self, step_A_time ) :
        self._step_A_times.append( step_A_time )
    
    """
    @param step_B_time Temps d'éxécution MOYEN pour le listage des Tweets avec
                       l'API Twitter publique.
    """
    def add_step_B_time ( self, step_A_time ) :
        self._step_A_times.append( step_A_time )
    
    """
    @param step_C_times Liste de temps d'éxécution pour indexer un Tweet.
    @param step_C_calculate_features_times Liste des temps d'éxécution pour
                                           calculer les caractéristiques des
                                           images d'un Tweet.
    @param _step_C_insert_into_times Liste des temps d'éxécution pour insérer
                                     un Tweet dans la BDD.
    """
    def add_step_C_times ( self, step_C_times, step_C_calculate_features_times, step_C_insert_into_times ) :
        self._step_C_times += step_C_times
        self._step_C_calculate_features_times += step_C_calculate_features_times
        self._step_C_insert_into_times += step_C_insert_into_times
    
    """
    @param step_C_times Liste de temps d'éxécution pour indexer un Tweet.
    """
    def add_step_D_times ( self, step_D_times ) :
        self._step_D_times += step_D_times
    
    """
    @param step_3_iteration_times Liste des temps d'éxécution pour itérer sur
                                  la base de données.
    @param step_3_usage_times Liste des temps d'éxécution de l'utilisation.
    """
    def add_step_3_times ( self, step_3_iteration_times, step_3_usage_times ) :
        self._step_3_iteration_times += step_3_iteration_times
        self._step_3_usage_times += step_3_usage_times
    
    """
    @return Une chaine de caractères à afficher.
    """
    def get_metrics ( self ) :
        to_print = ""
        if self._step_A_times != [] :
            to_print += "Temps moyen pour lister avec GOT3 : " + str(mean(self._step_A_times)) + "\n"
        if self._step_B_times != [] :
            to_print += "Temps moyen pour lister avec TwitterAPI : " + str(mean(self._step_B_times)) + "\n"
        if self._step_C_times != [] :
            to_print += "Temps moyen pour indexer avec GOT3 : " + str(mean(self._step_C_times)) + "\n"
        if self._step_C_calculate_features_times != [] :
            to_print += "Temps moyen pour indexer avec GOT3 : Calcul CBIR d'un Tweet : " + str(mean(self._step_C_calculate_features_times)) + "\n"
        if self._step_C_insert_into_times != [] :
            to_print += "Temps moyen pour indexer avec GOT3 : INSERT INTO d'un Tweet : " + str(mean(self._step_C_insert_into_times)) + "\n"
        if self._step_D_times != [] :
            to_print += "Temps moyen pour indexer avec TwitterAPI : " + str(mean(self._step_D_times)) + "\n"
        if self._step_3_iteration_times != [] :
            to_print += "Tempys moyen pour itérer lors de la recherche : " + str(mean(self._step_3_iteration_times)) + "\n"
        if self._step_3_usage_times != [] :
            to_print += "Tempys moyen pour comparer lors de la recherche : " + str(mean(self._step_3_usage_times)) + "\n"
        if to_print == "" :
            to_print = "Aucune statistique disponible ! Aucune requête n'a été lancée, ou le paramètre \"ENABLE_METRICS\" est à \"False\"."
        return to_print
