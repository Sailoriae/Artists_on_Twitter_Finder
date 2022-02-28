#!/usr/bin/python3
# coding: utf-8

import Pyro4


"""
Conteneur des moyennes des temps d'exécutions.
On ne stocke pas les mesures des temps d'exécutions, mais uniquement leur
somme, ainsi qu'un compte de mesures (Pour calculer la moyenne).
Permet d'optimiser l'espace occupé par le conteneur principal.
"""
class Mean_Container:
    def __init__ ( self ) :
        self._sum = 0 # Somme de toutes les valeurs ajoutées
        self._count = 0 # Compteur des valeurs ajoutées
    
    def add_one ( self, value ) :
        if value == None : return
        self._sum += value
        self._count += 1
    
    def add_many ( self, values ) :
        if values == None : return
        self._sum += sum( values )
        self._count += len( values )
    
    def get_mean ( self ) :
        if self._count == 0 : return None
        return self._sum / self._count
    
    def get_count ( self ) :
        return self._count


"""
Conteneur des mesures des temps d'exécutions.
"""
@Pyro4.expose
class Metrics_Container :
    def __init__ ( self ) :
        # Classe Tweets_Lister_with_SearchAPI
        self._step_A_times = Mean_Container()
        
        # Classe Tweets_Lister_with_TimelineAPI
        self._step_B_times = Mean_Container()
        
        # Classe Tweets_Indexer
        self._step_C_times = Mean_Container()
        self._step_C_download_image_times = Mean_Container()
        self._step_C_cbir_engine_times = Mean_Container()
        self._step_C_insert_into_times = Mean_Container()
        
        # Execution complète du Link Finder
        self._step_1_times = Mean_Container()
        
        # Itération sur la base de données
        self._step_3_times = Mean_Container()
        self._step_3_select_times = Mean_Container()
        self._step_3_iteration_times = Mean_Container()
        self._step_3_usage_times = Mean_Container()
        
        # Temps de traitement complet
        self._user_request_full_time = Mean_Container()
        self._scan_request_full_time = Mean_Container()
    
    """
    @param step_A_time Temps d'exécution MOYEN pour le listage des Tweets avec
                       la librairie SearchAPI.
    """
    def add_step_A_time ( self, step_A_time ) :
        self._step_A_times.add_one( step_A_time )
    
    """
    @param step_B_time Temps d'exécution MOYEN pour le listage des Tweets avec
                       l'API Twitter publique.
    """
    def add_step_B_time ( self, step_A_time ) :
        self._step_B_times.add_one( step_A_time )
    
    """
    @param step_C_times Liste de temps d'exécution pour indexer un Tweet.
    @param step_C_download_image_times Liste des temps pour télécharger une
                                       image d'un Tweet.
    @param step_C_cbir_engine_times Liste des temps d'exécution du moteur CBIR
                                    pour une image d'un Tweet.
    @param step_C_insert_into_times Liste des temps d'exécution pour insérer
                                    un Tweet dans la BDD.
    """
    def add_step_C_times ( self, step_C_times, step_C_download_image_times, step_C_cbir_engine_times, step_C_insert_into_times ) :
        self._step_C_times.add_many( step_C_times )
        self._step_C_download_image_times.add_many( step_C_download_image_times )
        self._step_C_cbir_engine_times.add_many( step_C_cbir_engine_times )
        self._step_C_insert_into_times.add_many( step_C_insert_into_times )
    
    """
    @param step_1_times Temps d'exécution global à l'étape 1.
    """
    def add_step_1_times ( self, step_1_times : float ) :
        self._step_1_times.add_one( step_1_times )
    
    """
    @param step_3_times Temps d'exécution pour faire la recherche inversée.
                        Doit être dans une liste.
    @param step_3_select_times Temps d'exécution du SELECT en SQL.
    @param step_3_iteration_times Liste des temps d'exécution pour itérer sur
                                  la base de données.
    @param step_3_usage_times Liste des temps d'exécution de l'utilisation.
    """
    def add_step_3_times ( self, step_3_times, step_3_select_times, step_3_iteration_times, step_3_usage_times ) :
        self._step_3_times.add_many( step_3_times )
        self._step_3_select_times.add_one( step_3_select_times )
        self._step_3_iteration_times.add_many( step_3_iteration_times )
        self._step_3_usage_times.add_many( step_3_usage_times )
    
    """
    Enregistrer le temps de traitement complet d'une requête utilisateur.
    @param scan_request_full_time Temps d'exécution.
    """
    def add_user_request_full_time ( self, user_request_full_time : float ) :
        self._user_request_full_time.add_one( user_request_full_time )
    
    """
    Enregistrer le temps de traitement complet d'une requête de scan.
    @param scan_request_full_time Temps d'exécution.
    """
    def add_scan_request_full_time ( self, scan_request_full_time : float ) :
        self._scan_request_full_time.add_one( scan_request_full_time )
    
    """
    @return Une chaine de caractères à afficher.
    """
    def get_metrics ( self ) :
        to_print = ""
        
        if self._step_A_times.get_count() != 0 :
            to_print += f"Etape A : Temps moyen pour lister avec SearchAPI : {self._step_A_times.get_mean()} ({self._step_A_times.get_count()} listages)\n"
        
        if self._step_B_times.get_count() != 0 :
            to_print += f"Etape B : Temps moyen pour lister avec TimelineAPI : {self._step_B_times.get_mean()} ({self._step_B_times.get_count()} listages)\n"
        
        if self._step_C_times.get_count() != 0 :
            to_print += f"Etape C : Temps moyen pour indexer : {self._step_C_times.get_mean()} ({self._step_C_times.get_count()} Tweets)\n"
        if self._step_C_download_image_times.get_count() != 0 :
            to_print += f" - Dont : Téléchargement d'une image : {self._step_C_download_image_times.get_mean()} ({self._step_C_download_image_times.get_count()} images)\n"
        if self._step_C_cbir_engine_times.get_count() != 0 :
            to_print += f" - Dont : Calcul de l'empreinte d'une image : {self._step_C_cbir_engine_times.get_mean()} ({self._step_C_cbir_engine_times.get_count()} images)\n"
        if self._step_C_insert_into_times.get_count() != 0 :
            to_print += f" - Dont : Enregistrement d'un Tweet : {self._step_C_insert_into_times.get_mean()} ({self._step_C_insert_into_times.get_count()} Tweets)\n"
        
        if self._step_1_times.get_count() != 0 :
            to_print += f"Etape 1 : Temps moyen pour passer dans le Link Finder : {self._step_1_times.get_mean()} ({self._step_1_times.get_count()} exécutions)\n"
        
        if self._step_3_times.get_count() != 0 :
            to_print += f"Etape 3 : Temps moyen pour rechercher sur un compte : {self._step_3_times.get_mean()} ({self._step_3_times.get_count()} recherches de {int(self._step_3_usage_times.get_count()/self._step_3_times.get_count())} comparaisons en moyenne)\n"
        if self._step_3_select_times.get_count() != 0 :
            to_print += f" - Dont : Obtenir les Tweets enregistrés : {self._step_3_select_times.get_mean()} ({self._step_3_select_times.get_count()} requêtes)\n"
        if self._step_3_iteration_times.get_count() != 0 :
            to_print += f" - Dont : Itérer sur les Tweets : {self._step_3_iteration_times.get_mean()} ({self._step_3_iteration_times.get_count()} itérations)\n"
        if self._step_3_usage_times.get_count() != 0 :
            to_print += f" - Dont : Comparer les empreintes : {self._step_3_usage_times.get_mean()} ({self._step_3_usage_times.get_count()} images)\n"
        
        if self._user_request_full_time.get_count() != 0 :
            to_print += f"Temps moyen pour traiter une requête utilisateur : {self._user_request_full_time.get_mean()} ({self._user_request_full_time.get_count()} requêtes)\n"
        if self._scan_request_full_time.get_count() != 0 :
            to_print += f"Temps moyen pour traiter une requête de scan : {self._scan_request_full_time.get_mean()} ({self._scan_request_full_time.get_count()} requêtes)\n"
        
        if to_print == "" :
            to_print = "Aucune moyenne disponible, car aucune requête n'a été lancée."
        else :
            to_print = "Les temps suivants sont exprimés en secondes.\n" + to_print[:-1] # On enlève le dernier \n
        
        return to_print
