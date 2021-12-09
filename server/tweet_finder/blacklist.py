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

Note 7 : Les japonais (Entreprises ou personnes) tweetent BEAUCOUP TROP !

Source intéressante : Top 100 des plus gros comptes Twitter classés par nombre
de Tweets publiés : https://phlanx.com/top/twitter/tweets/100
Attention : Il y en a qui ont beaucoup de Tweets mais peu de médias, ne pas les
ajouter ici !
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

              # === BOTS ANIMES ===
              1210828729204662274, # @anime_Mika_bot

              # === BOTS MLP ===
              1140709486597984256, # @hourlypony
              1857039733, # @EmergencyPony
              1040873635110690816, # @StarbotGlimmer
              1303671355406073856, # @dailyapplejack
              630915843, # @CalpainEqD

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

              # === BOTS "EVERY FRAME OF" ===
              1359609677223518212, # @shrekframe
              1123667940228911104, # @SbFramesInOrder
              1407213284495826954, # @breaking_frames
              1285312394286292994, # @OneFrameSimpson
              1156296787298267136, # @SpidrVrseFrames
              1371209401437159427, # @BeeMovieFrames
              1367937917474254850, # @LOTRFrames
              1450443427330633735, # @efgfio

              # === BOTS DIVERS ===
              3032932864, # @MostwantedHFRES
              1680484418, # @Jasmine_Eq00
              68956490, # @RedScareBot
              56870353, # @onlinelisting
              2364474198, # @mylittle06

              # === REPOSTS MANUELS ===
              1049263783573643264, # @_Miku_Lover
              598505436, # @Kanerudo66

              # === JOURNAUX ANGLOPHONES ===
              807095, # @nytimes
              759251, # @CNN
              428333, # @cnnbrk
              742143, # @BBCWorld
              2467791, # @washingtonpost
              3108351, # @WSJ (Wall Street Journal)
              14293310, # @TIME
              1652541, # @Reuters
              5988062, # @TheEconomist
              18949452, # @FT (Financial Times)

              # === JOURNAUX NON-ANGLOPHONES ===
              15007299, # @ElNacionalWeb
              108192135, # @EP_Mundo
              165796189, # @geonews_urdu

              # === ACTUALITE (JOURNAUX ?) ===
              225647847, # @info_Ve
              171299971, # @CaraotaDigital
              1179710990, # @OccuWorld
              243133079, # @Rojname_com
              213165296, # @SiguesTeSigo

              # === ENTREPRISES (USA) ===
              15518000, # @urbandictionary
              85741735, # @AmazonHelp
              20536157, # @Google
              10228272, # @YouTube
              20793816, # @amazon
              16573941, # @netflix
              11348282, # @NASA
              17471979, # @NatGeo
              17842366, # @Discovery
              67418441, # @Disney
              393852070, # @Avengers
              15687962, # @Marvel
              18173624, # @DCComics

              # === ENTREPRISES (EUROPE) ===
              92335697, # @DisneyFR

              # === ENTREPRISES (JAPON & COREE) ===
              116397707, # @ototoy_info
              100200469, # @skream_japan
              115639376, # @akiko_lawson
              4823945834, # @Love_McD
              132355708, # @711SEJ
              561669474, # @asahibeer_jp
              2213312341, # @ILOHAS
              89142182, # @famima_now
              2316574981, # @GalaxyMobileJP
              133684052, # @suntory
              1388673048, # @Fanta_Japan
              130426181, # @GEORGIA_JAPAN
              717628618906570752, # @asahiinryo_jp
              104120518, # @AQUARIUS_SPORTS
              188233441, # @KFC_jp
              184004752, # @McDonaldsJapan
              1346933186, # @lovelive_SIF
              393339671, # @gusto_official
              120655299, # @disneyjp
              378692212, # @disneystudiojp
              1139077015393357824, # @DisneyStudioJ_A
              992724372648480768, # @shopDisneyjp
              826756376504381441, # @starwarsjapan
              1587275148, # @MezzoMikiD
              1011356094797570048, # @DisneyPlusJP
              864437453800620032, # @MarvelStudios_J
              278549221, # @warnerjp
              804279340842160134, # @SpidermanfilmJP
              3254815086, # @NetflixJP
              800990438794489857, # @marvel_jp
              892532460675661824, # @dc_jp
              953531334160338949, # @VenomMovieJP

              # === ENTREPRISES (AUTRES) ===
              155409802, # @TelkomCare
              255409050, # @Telkomsel
              124172948, # @la_patilla

              # === PERSONNES ===
              63299591, # @VENETHIS
              2669983818, # @test5f1798
              2050001283, # @cas_2050001283
              3012764258, # @87095
              120421476, # @kakusan_RT
              19272300, # @DEALSANDSTEALss
              23719043, # @dc2net
              486288760, # @hkTjee
              121190725, # @henrirouen
             ]
