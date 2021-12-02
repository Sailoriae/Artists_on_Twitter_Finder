#!/usr/bin/python3
# coding: utf-8


import sys
print( "Ne pas exécuter ce script sans savoir ce qu'il fait." )
sys.exit(0)


"""
Lire d'abord le document "Pistes_explorées_pour_la_recherche.md" !

Cette classe permet au serveur AOTF de faire de la recherche de vecteurs
similaires via un graphe des vecteurs.
Problème : C'est horriblement lent ! Car les données sont éloignées du code.
Il vaut largement mieux utiliser Milvus ou quelque chose de la sorte, qui est
un SGDB développé par des pros du sujet.

IMPORTANT :
Si jamais on indexe deux images proches en parallèle, il n'y aura pas de lien
entre elles. Il faut donc un sémaphore pour bloquer l'indexation parallèle.
"""

import numpy as np

# Les importations se font depuis le répertoire racine du serveur AOTF
# Ainsi, si on veut utiliser ce script indépendamment (Notamment pour des
# tests), il faut que son répertoire de travail soit ce même répertoire
if __name__ == "__main__" :
    from os.path import abspath as get_abspath
    from os.path import dirname as get_dirname
    from os import chdir as change_wdir
    change_wdir(get_dirname(get_abspath(__file__)))
#    change_wdir( "../.." ) # Ce fichier était destiné à être dans le répertoire "database"
    change_wdir( "../server" )

from tweet_finder.database.class_SQLite_or_MySQL import SQLite_or_MySQL
import parameters as param

if param.USE_MYSQL_INSTEAD_OF_SQLITE :
    import mysql.connector


CBIR_LIST_LENGHT = 240

"""
Dans le graphe, on calcul la distance de Manhattan entre les vecteurs stockés.
On ne fait surtout pas comme dans la classe "CBIR_Engine".
Cela permet d'avoir une méthode rapide et différence de celles utilisée dans
la classe CBIR_Engine.
"""
def vectors_distance ( vector_1, vector_2 ) :
    return float( np.sum( np.fabs( np.float32(vector_1) - np.float32(vector_2) ) ) )

# Le seuil pour dire que deux images sont les mêmes est de 1% de la distance
# entre deux points les plus opposés des histogrammes possibles.
SEUIL = vectors_distance( [0]*240, [1]*240 ) * 0.01


SQL_GET_START_NODE = "SELECT image_id, image_table_id FROM tweet_images_graph_nodes ORDER BY node_uses_count DESC LIMIT 1"
SQL_GET_CONNECTED_NODES_1 = "SELECT image_1_id, image_1_table_id, distance FROM tweet_images_graph WHERE image_2_id = %s"
SQL_GET_CONNECTED_NODES_2 = "SELECT image_2_id, image_2_table_id, distance FROM tweet_images_graph WHERE image_1_id = %s"
SQL_COUNT_GET_VECTOR = "UPDATE tweet_images_graph_nodes SET node_uses_count = node_uses_count + 1 WHERE image_id = %s"
SQL_GET_VECTOR_TABLE_1 = "SELECT * FROM tweets INNER JOIN tweets_images_1 ON tweets.tweet_id = tweets_images_1.tweet_id WHERE image_name = %s"
SQL_GET_VECTOR_TABLE_2 = "SELECT * FROM tweets INNER JOIN tweets_images_2 ON tweets.tweet_id = tweets_images_2.tweet_id WHERE image_name = %s"
SQL_GET_VECTOR_TABLE_3 = "SELECT * FROM tweets INNER JOIN tweets_images_3 ON tweets.tweet_id = tweets_images_3.tweet_id WHERE image_name = %s"
SQL_GET_VECTOR_TABLE_4 = "SELECT * FROM tweets INNER JOIN tweets_images_4 ON tweets.tweet_id = tweets_images_4.tweet_id WHERE image_name = %s"
SQL_GET_NODE = "SELECT * FROM tweet_images_graph_nodes WHERE image_id = %s"
SQL_GET_NODE_LINK = "SELECT * FROM tweet_images_graph WHERE image_1_id = %s AND image_2_id = %s"
SQL_ADD_NODE = "INSERT INTO tweet_images_graph_nodes ( image_id, image_table_id ) VALUES ( %s, %s )"
SQL_ADD_NODE_LINK = "INSERT INTO tweet_images_graph ( image_1_id, image_1_table_id, image_2_id, image_2_table_id, distance ) VALUES ( %s, %s, %s, %s, %s)"
SQL_DELETE_LINK = "DELETE FROM tweet_images_graph WHERE image_1_id = %s AND image_2_id = %s"

if not param.USE_MYSQL_INSTEAD_OF_SQLITE :
    SQL_GET_CONNECTED_NODES_1 = SQL_GET_CONNECTED_NODES_1.replace( "%s", "?" )
    SQL_GET_CONNECTED_NODES_2 = SQL_GET_CONNECTED_NODES_2.replace( "%s", "?" )
    SQL_COUNT_GET_VECTOR = SQL_COUNT_GET_VECTOR.replace( "%s", "?" )
    SQL_GET_NODE = SQL_GET_NODE.replace( "%s", "?" )
    SQL_ADD_NODE = SQL_ADD_NODE.replace( "%s", "?" )
    SQL_ADD_NODE_LINK = SQL_ADD_NODE_LINK.replace( "%s", "?" )
    SQL_GET_VECTOR_TABLE_1 = SQL_GET_VECTOR_TABLE_1.replace( "%s", "?" )
    SQL_GET_VECTOR_TABLE_2 = SQL_GET_VECTOR_TABLE_2.replace( "%s", "?" )
    SQL_GET_VECTOR_TABLE_3 = SQL_GET_VECTOR_TABLE_3.replace( "%s", "?" )
    SQL_GET_VECTOR_TABLE_4 = SQL_GET_VECTOR_TABLE_4.replace( "%s", "?" )
    SQL_DELETE_LINK = SQL_DELETE_LINK.replace( "%s", "?" )


"""
Le graphe doit être en une seule partie !

Deux tables SQL :
- Table des noeuds du graphe ("tweet_images_graph_nodes"), sert uniquement à
  stocker les compteurs de passages dans les noeuds pour déterminer le noeud
  de départ.
- Table des liens du graphe ("tweet_images_graph"), permet de faire la
  recherche de vecteurs similaires.
"""
class Graph_Search ( SQLite_or_MySQL ) :
    def __init__ ( self ) :
        super().__init__()
                
        c = self.get_cursor()
        
        # Construction des tables et des indexes dans le cas d'une BDD MySQL
        if param.USE_MYSQL_INSTEAD_OF_SQLITE :
            c.execute( """CREATE TABLE IF NOT EXISTS tweet_images_graph_nodes (
                              image_id VARCHAR(19) PRIMARY KEY,
                              image_table_id TINYINT UNSIGNED,
                              node_uses_count BIGINT UNSIGNED DEFAULT 0 )""" )
            
            c.execute( """CREATE TABLE IF NOT EXISTS tweet_images_graph (
                              image_1_id VARCHAR(19),
                              image_1_table_id TINYINT UNSIGNED,
                              image_2_id VARCHAR(19),
                              image_2_table_id TINYINT UNSIGNED,
                              distance FLOAT UNSIGNED )""" )
            
            try :
                c.execute( "CREATE INDEX image_1_id ON tweet_images_graph ( image_1_id )" )
                c.execute( "CREATE INDEX image_2_id ON tweet_images_graph ( image_2_id )" )
            except mysql.connector.errors.ProgrammingError : # L'index existe déjà
                pass
        
        # Construction des tables et des indexes dans le cas d'une BDD SQLite
        else :
            c.execute( """CREATE TABLE IF NOT EXISTS tweet_images_graph_nodes (
                              image_id VARCHAR(19) PRIMARY KEY,
                              image_table_id UNSIGNED TINYINT,
                              node_uses_count UNSIGNED BIGINT DEFAULT 0 )""" )
            
            c.execute( """CREATE TABLE IF NOT EXISTS tweet_images_graph (
                              image_1_id VARCHAR(19),
                              image_1_table_id UNSIGNED TINYINT,
                              image_2_id VARCHAR(19),
                              image_2_table_id UNSIGNED TINYINT,
                              distance UNSIGNED FLOAT )""" )
            
            c.execute( "CREATE INDEX IF NOT EXISTS image_1_id ON tweet_images_graph ( image_1_id )" )
            c.execute( "CREATE INDEX IF NOT EXISTS image_2_id ON tweet_images_graph ( image_2_id )" )
        
        self.conn.commit()
        
        self.EMPTY_GRAPH = False
    
    """
    Obtenir l'image = le noeud sur lequel on est le plus passé.
    @return Un tuple contenant :
            - L'ID de l'image.
            - L'ID de la table dans laquelle le vecteur de l'image est présent.
    """
    def get_start_node ( self ) :
        cursor = self.get_cursor()
        cursor.execute( SQL_GET_START_NODE )
        return cursor.fetchone()
    
    """
    Obtenir la liste des images = des noeuds connectés à une image = un noeud.
    @param node_image_id L'ID de l'image.
    @return Une liste de tuples contenant :
            - L'ID de l'image = du noeud connecté.
            - L'ID de la table dans laquelle le vecteur de l'image est présent.
            - Sa distance avec l'image = le noeud passé en paramètre.
    """
    def get_connected_nodes ( self, node_image_id ) :
        to_return = []
        cursor = self.get_cursor()
        cursor.execute( SQL_GET_CONNECTED_NODES_1, (node_image_id,) )
        to_return.extend( cursor.fetchall() )
        cursor.execute( SQL_GET_CONNECTED_NODES_2, (node_image_id,) )
        to_return.extend( cursor.fetchall() )
        return to_return
    
    """
    Obtenir le vecteur d'une image = d'un noeud.
    @param node_image_id L'ID de l'image.
    @param node_image_table_id L'ID de la table dans laquelle le vecteur de
                               l'image est présent [1-4].
    @return Un tuple contenant :
            - Le vecteur des caractéristiques de cette image.
            - La liste des données associées à cette image.
    """
    def get_vector ( self, node_image_id, node_image_table_id ) :
        cursor = self.get_cursor()
        cursor.execute( SQL_COUNT_GET_VECTOR, (node_image_id,) )
        self.conn.commit()
        
        if node_image_table_id == 1 :
            cursor.execute( SQL_GET_VECTOR_TABLE_1, (node_image_id,) )
        elif node_image_table_id == 2 :
            cursor.execute( SQL_GET_VECTOR_TABLE_2, (node_image_id,) )
        elif node_image_table_id == 3 :
            cursor.execute( SQL_GET_VECTOR_TABLE_3, (node_image_id,) )
        elif node_image_table_id == 4 :
            cursor.execute( SQL_GET_VECTOR_TABLE_4, (node_image_id,) )
        else :
            raise RuntimeError( "Le paramètre \"node_image_table_id\" doit être compris entre 1 et 4 !" )
        
        data = cursor.fetchone()
        return data[ 5 : 5+CBIR_LIST_LENGHT ], data[ : 5 ]
    
    """
    Recherche de vecteurs similaires :
    Recherche les images = les noeuds les plus proche dans le graphe des
    vecteurs.
    @param input_vector Le vecteur des caractéristiques de l'image à chercher.
    @param current_node_image_id Ne pas utiliser (Récursivité).
    @param explored_nodes_image_id Ne pas utiliser (Récursivité).
    @return Une liste de tuples contenant :
            - L'ID de l'image considérée comme proche.
            - L'ID de la table dans laquelle le vecteur de l'image est présent.
            - La distance entre cette image et l'image à chercher.
            - La liste des données associées à cette image.
    La liste de retour contient obligatoirement un tuple, ou plusieurs si on
    est en dessous de la valeur "SEUIL".
    """
    def search_in_graph ( self, input_vector,
                                current_node_tuple = None,
                                explored_nodes_images_ids = [] ) :
        if current_node_tuple == None :
            start_node = self.get_start_node()
            if start_node == None : return [] # Pour le premier ajout dans le graphe
            image_id, image_table_id = start_node
            vector, data = self.get_vector( image_id, image_table_id )
            current_node_tuple = ( image_id,
                                   image_table_id,
                                   vectors_distance( vector, input_vector ),
                                   data )
            
            # On ajoute le noeud à la liste des noeuds explorés
            explored_nodes_images_ids.append( current_node_tuple[0] )
        
        to_return = []
        closest = current_node_tuple
        
        # Pour tous les noeuds connectés au noeud courant
        for ( connected_node_image_id,
              connected_node_image_table_id,
              current_distance) in self.get_connected_nodes( current_node_tuple[0] ) :
            # Si le noeud connecté a déjà été exploré, on le passe
            if connected_node_image_id in explored_nodes_images_ids :
                continue
            
            # Ajouter le noeud connecté à la liste des noeuds explorés
            explored_nodes_images_ids.append( connected_node_image_id )
            
            # Obtenir la distance de l'image du noeud connecté avec l'image de
            # requête, et l'associer avec ses données
            test_vector, data = self.get_vector( connected_node_image_id, connected_node_image_table_id )
            test_distance = vectors_distance( test_vector, input_vector )
            test_node_tuple = ( connected_node_image_id,
                                connected_node_image_table_id,
                                test_distance,
                                data )
            
            # Si ce noeud connecté est en dessous du seuil, il faut le retourner
            if test_distance < SEUIL :
                to_return.append( test_node_tuple )
            
            # Si ce noeud connecté est plus proche que l'actuel, il faut aller
            # explorer ses noeuds connectés
            if test_distance < current_node_tuple[2] :
                # On filtre la liste des noeuds retournés (A cause du
                # fait qu'on doit forcément retourner un noeud le plus proche,
                # il faut mettre à jour notre noeud le plus proche si jamais
                # la fonction a retourné un noeud dont la distance est
                # supérieure à SEUIL)
                for found_nodes in self.search_in_graph( input_vector,
                                                         current_node_tuple = test_node_tuple,
                                                         explored_nodes_images_ids = explored_nodes_images_ids ) :
                    # Si le noeud retourné est en dessous du seuil, il faut
                    # le retourner
                    if closest[1] < SEUIL :
                        to_return.append( found_nodes )
                    
                    # On met forcément à jour le noeud le plus proche
                    if closest == None or found_nodes[1] < closest[1] :
                        closest = found_nodes
            
            # On met forcément à jour le noeud le plus proche
            if closest == None or closest[1] < test_distance :
                closest = test_node_tuple
        
        # Si on n'a trouvé aucun noeud, on retourne forcément le noeud le plus
        # proche qu'on ait trouvé
        if len(to_return) == 0 :
            if closest != None :
                to_return.append( closest )
        
        return to_return
    
    """
    Ajouter une image = un noeud dans le graphe des vecteurs.
    @param node_image_id L'ID de l'image (Doit correspondre à la table des
                         images de Tweets).
    @param node_image_table_id L'ID de la table dans laquelle le vecteur de
                               l'image est présent [1-4].
    @param node_vector Le vecteur des caractéristiques de l'image à ajouter.
    """
    def add_node ( self, node_image_id, node_image_table_id, node_vector ) :
        # Vérifier avant que cette image = ce noeud n'ait pas déjà été ajouté
        cursor = self.get_cursor()
        cursor.execute( SQL_GET_NODE, ( node_image_id, ) )
        if cursor.fetchone() != None : return
        
        # Liste des liens des noeuds auxquels on s'est connecté
        connected_nodes_of_connected_nodes = []
        
        # Se connecter aux noeuds les plus proches
        for node_tuple in self.search_in_graph( node_vector ) :
            if node_tuple[2] < SEUIL :
                for ( connected_node_image_id,
                      connected_node_image_table_id,
                      distance) in self.get_connected_nodes( node_tuple[0] ) :
                    connected_nodes_of_connected_nodes.append(
                        ( node_tuple[0], connected_node_image_id, distance ) )
            
            if node_image_id == node_tuple[0] :
                raise RuntimeError( "On ajoute un lien avec nous-même, c'est pas normal !" )
            
            cursor = self.get_cursor()
            
            # Vérifier avant que le lien n'existe pas déjà
            cursor.execute( SQL_GET_NODE_LINK, ( node_image_id, node_tuple[0] ) )
            if cursor.fetchone() != None : continue
            cursor.execute( SQL_GET_NODE_LINK, ( node_tuple[0], node_image_id ) )
            if cursor.fetchone() != None : continue
            
            # Créer le lien
            cursor.execute( SQL_ADD_NODE_LINK, ( node_image_id,
                                                 node_image_table_id,
                                                 node_tuple[0],
                                                 node_tuple[1],
                                                 node_tuple[2] ) )
            self.conn.commit()
        
        # Chercher si tous les liens des noeuds auxquels on s'est connectés
        # sont des liens forcés
        forced_links_count = 0
        closest = None
        closest_distance = None
        for image_1_id, image_2_id, link_distance in connected_nodes_of_connected_nodes :
            if closest == None or link_distance < closest_distance :
                closest = image_2_id
                closest_distance = link_distance
            if link_distance >= SEUIL :
                forced_links_count += 1
        
        # Si tous les liens des noeuds auxquels on s'est connecté sont des
        # liens forcés, il faut en garder un seul, celui avec la plus courte
        # distance
        if forced_links_count >= len( connected_nodes_of_connected_nodes ) :
            new_list = []
            for image_1_id, image_2_id, link_distance in connected_nodes_of_connected_nodes :
                if image_2_id != closest :
                    new_list.append( ( image_1_id, image_2_id, link_distance ) )
            connected_nodes_of_connected_nodes = new_list
        
        # Supprimer les liens forcés des noeuds connectés auxquels on s'est
        # connecté
        for image_1_id, image_2_id, link_distance in connected_nodes_of_connected_nodes :
            if link_distance >= SEUIL :
                cursor = self.get_cursor()
                cursor.execute( SQL_DELETE_LINK, ( image_1_id, image_2_id ) )
                cursor.execute( SQL_DELETE_LINK, ( image_2_id, image_1_id ) )
                self.conn.commit()
        
        # Ajouter le noeud dans la liste des noeuds
        cursor = self.get_cursor()
        cursor.execute( SQL_ADD_NODE, ( node_image_id, node_image_table_id ) )
        self.conn.commit()
