#!/usr/bin/python3
# coding: utf-8

"""
LISTE NOIRE DES COMPTES A NE PAS INDEXER !
Ceci est une liste d'IDs de comptes Twitter qui sont connus pour avoir une
grande quantité de Tweets avec des medias, mais qui ne sont pas des artistes.
Par exemple : Des robots postant des illustrations.

Note 1 : Eviter de mettre dans cette liste les comptes qui ont moins de
quelques milliers de Tweets avec médias. Sauf si on sait par avance qu'il vont
exploser.

Note 2 : Les artistes qui Tweetent beaucoup (Même si c'est des screenshots de
leur partie d'Animal Crossing) ne doivent pas être dans cette liste !

Note 3 : Il est impossible que cette liste soit exhaustive. Mais elle permet de
désindexer facilement des comptes si jamais quelqu'un s'amuse à nous faire
indexer des gros comptes inutiles.

Note 4 : Twitter ne réalloue pas un ID de compte supprimé, donc on peut ne pas
vérifier l'existence des comptes présents dans cettte liste.

Note 5 : Afin d'optimiser la place en mémoire vive, cette liste doit être
chargée une seule fois, dans la mémoire partagée !

Note 6 : Ces comptes sont considérés comme invalides, et sont donc exclus lors
de l'étape du Link Finder.
"""
BLACKLIST = [ # === GROUPES DE BOTS ===
              1033769492575338496, # @PonyPicsBot
              1033995940187844608, # @SceneryPonyPics
              1185937069773852672, # @SFWDerpiUp
              1216705284082688001, # @MikuMikuPics
              1033735833851977728, # @Lewdlestia
              1096446122514661377, # @Lunhorny
              1172427334575476736, # @NSFWDerpiUp

              2910211797, # @AcePictureBot
              3247124434, # @AceYuriBot
              3530068521, # @AceCatgirlBot
              3283566394, # @AceAsianBot

              # === BOTS HENTAI ===
              1125035851581415426, # @alewdfemboy
              1365081510945173506, # @alewdbunnygirl
              1412147722942025731, # @tasteful_ecchi
              1331656963541897216, # @lewdxsthetic
              1158044571651231744, # @ecchi_aesth
              762132880990543872, # @AhegaoOnline
              952716530122461184, # @sissyslutbton

              # === BOTS FURRY ===
              995052384777842689, # @YiffHourly
              1128143986617663488, # @OwO_Butt
              34945778, # @sniperfoxdls

              # === BOTS DE MEMES ===
              762799939395158016, # @WholesomeMeme
              1349856571988258826, # @OldMemeArchive
              1166686636568207361, # @MinecraftMeme16
              1035856038912827392, # @memecrashes
              1151151821437722624, # @traabot

              # === REPOSTS MANUELS ===
              1049263783573643264, # @_Miku_Lover
             ]
