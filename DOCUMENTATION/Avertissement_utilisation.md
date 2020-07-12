# Avertissement sur l'utilisation

Plus un serveur a eu de requêtes, plus il fait grandir sa base de données.

Si un serveur tout neuf reçoit beaucoup de requêtes, il va avoir beaucoup de comptes Twitter à indexer entièrement, et c'est une étape extrèmement longue. Comme on ne peut indexer qu'un seul compte Twitter à la fois, les requêtes risquent de prendre beaucoup de temps à être traitées entièrement.

Le problème est encore plus grand si on tombe sur un compte Twitter d'artiste avec énormément de médias.
Par exemple : @MayoRiyo, avec actuellement (juillet 2020) plus de 17 000 médias, dont plus de 16 000 images !
Un tel compte crée un bouchon dans le pipeline.


**Mais pourquoi ne peut-on pas indexer plusieurs comptes Twitter en même temps ?**

Parce qu'il y a des limites sur l'API Twitter, et qui cela prend plus de temps de chercher tous les tweets deux comptes en même temps que de le faire à la suite.

Cependant, dans le cas d'un très gros compte qui boucherait le pipeline, cela serait intéressant. A tester !


**Et pourquoi ne pas partager les bases de données entre serveurs ?**

Parce qu'on ne peut pas maitriser le cas où quelqu'un metterait de fausses données dans le réseau... Pour embêter le monde !
Donc on ne fais confiance à personne.
