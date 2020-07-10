#!/usr/bin/python3
# coding: utf-8


"""
Ajouter un argument à une URL.
@param url L'URL à traiter.
@param argument L'argument à ajouter, par exemple : "name=large".
@return L'URL avec l'argument ajouté.
"""
def add_argument_to_url( url : str, argument : str ) :
    if "?" in url :
        if url[-1] == "?" :
            return url + argument
        else :
            return url + "&" + argument
    else :
        return url + "?" + argument


"""
Test du bon fonctionnement de cette fonction
"""
if __name__ == '__main__' :
    test1 = add_argument_to_url( "http://test.com", "param=test" )
    result1 = "http://test.com?param=test"
    test2 = add_argument_to_url( "http://test.com?", "param=test" )
    result2 = "http://test.com?param=test"
    test3 = add_argument_to_url( "http://test.com?test=param", "param=test" )
    result3 = "http://test.com?test=param&param=test"
    
    if test1 == result1 and test2 == result2 and test3 == result3:
        print( "Test OK !" )
    else :
        print( "Test échoué !" )
