import random

class Domino:
    def __init__(self, d:tuple):
        self.d=d #domino sous la forme d'un couple d'entiers
        self.double=(d[0]==d[1]) #test : double ou non ?
    def t(self):
        return self.d
    def db(self):
        return self.double
    def val(self):
        return self.d[0]+self.d[1]
    def inv(self):
        if not self.double:
            self.d=(self.d[1], self.d[0]) #fct qui inverse les deux positions

class Chain: #jeu en cours
    def __init__(self, ld:list[Domino]):
        self.c:list[Domino]=[d for d in ld]
        self.right=ld[len(ld)-1].t()[1] #valeur du domino tt a droite
        self.left=ld[0].t()[0] #valeur du domino tt a gauche
    def ex(self):
        return self.left, self.right
    def dom_list(self):
        return self.c
    def plateau(self):
        return [d.t() for d in self.c]
    def push(self, d:Domino, ex:str): #pour effectuer un nouveau coup
        if ex=='right': #si on peut jouer sur le domino de droite
            self.c.append(d) #on ajt ce domino au jeu
            self.right=d.t()[1] #on considère la nvl valeur de droite
        else:
            tempo=[d]
            for dom in self.c:
                tempo.append(dom)
            self.c=[dom for dom in tempo] #on ajoute le domino a gauche
            self.left=d.t()[0] #on considere la nvl valeur de gauche

ensemble : list[Domino] = [Domino((i,j)) for i in range(7) for j in range(i,7)]

def distribute(jeu, np) :
    #jeu_p1 = []
    #jeu_p2 = []
    jeu_p={} #jeu_p[i] est le jeu du ieme joueur
    talon = []
    random.shuffle(jeu)  #melange le jeu a chaque fois
    biggest_domino=jeu[0]
    beginning_p=1
    db=jeu[0].db()
    taille_jeu=len(jeu)//(np+1)
    for i in range(len(jeu)//(np+1)): #on repartit les cartes. le reste est mis dans le talon
        for j in range(np):
            if j+1 in jeu_p:
                jeu_p[j+1].append(jeu[j*taille_jeu +i])
            else:
                jeu_p[j+1]=[jeu[j*taille_jeu +i]]
            if db:
                if jeu[j*taille_jeu+i].db():
                    if jeu[j*taille_jeu+i].t()[0] > biggest_domino.t()[0]:
                        biggest_domino = jeu[j*taille_jeu+i]
                        beginning_p = j+1
            else:
                if jeu[j*taille_jeu+i].db():
                    biggest_domino = jeu[j*taille_jeu+i]
                    beginning_p = j+1
                    db = True
                else:
                    if jeu[j*taille_jeu+i].val() > biggest_domino.val():
                        biggest_domino = jeu[j*taille_jeu+i]
                        beginning_p = j+1
        talon.append(jeu[np * taille_jeu + i])
    if len(jeu)%(np+1) !=0 :
        for i in range(len(jeu)%(np+1)) :
            talon.append(jeu[(np+1)*taille_jeu + i])
    return jeu_p, talon, beginning_p, biggest_domino

def guess_repartition_1p(l, taille_jeu):
    assert taille_jeu<=len(l)
    all_guesses=[]
    for delay in range(len(l)-taille_jeu+1):
        for i in range(taille_jeu):
            for j in range(len(l)-taille_jeu+1-delay):
                if j==0 and i!=0:
                    continue
                if i==0 and j!=0:
                    continue
                else:
                    associated={}
                    guess, talon=[],[]
                    for k in range(taille_jeu-i):
                        guess.append(l[k+delay])
                        associated[l[k+delay].t()]=1
                    for k in range(i):
                        guess.append(l[taille_jeu-i+j+k+delay])
                        associated[l[taille_jeu-i+j+k+delay].t()]=1
                    for d in l:
                        if not (d.t() in associated):
                            talon.append(d)
                    all_guesses.append((guess, talon))
    return all_guesses

def complementary(l, sl):
    known={}
    comp=[]
    for d in sl:
        known[d.t()]=1
    for d in l:
        if not d.t() in known:
            comp.append(d)
    return comp

def guess_repartition(l:list[Domino], tailles_jeux:list[int], cp):
    guesses=guess_repartition_1p(l, tailles_jeux[cp-1])
    if cp==len(tailles_jeux):
        return [r for r in guesses]
    else:
        repart=[]
        for g in guesses:
            comp=complementary(l, g[0])
            further=guess_repartition(comp, tailles_jeux, cp+1)
            for r in further:
                repart.append((g[0],)+r)
        return repart

def anonymous_dominos(jeu_ia, current_game:Chain):
    lad=[]
    known={}
    for d in jeu_ia:
        known[d.t()]=1
    for d in current_game.plateau():
        known[d]=1
    for d in ensemble:
        if not (d.t() in known):
            lad.append(d)
    return lad

def can_play(jeu_p, plateau) :
    left, right = plateau.ex()
    for d in jeu_p :
        dom = d.t()
        if left in [dom[0], dom[1]] :
            return True #...je cherche a acceder au domino qui peut etre joue
        elif right in [dom[0], dom[1]] :
            return True
    return False

def playable_dominos(jeu_p, plateau) :
    playable = []
    for d in jeu_p :
        if can_play([d], plateau): #cela va nous dire si on peut jouer le domino d
            playable.append(d)
    return playable

def remove(d, pile):
    for i in range(len(pile)):
        if pile[i]==d:
            pile[i], pile[len(pile)-1]=pile[len(pile)-1], pile[i] #on echange les pos pour appliquer pop
            pile.pop()
            break #on sort de la boucle pour eviter des recursions inutiles qd on a trv d

def choose_alea(playable_dominos):
    return random.randint(0,len(playable_dominos)-1)

def choose_naive(playable_dominos) :
    valeur_max = 0
    domino_max = 0
    for i in range(len(playable_dominos)) :
        if valeur_max < playable_dominos[i].val() :
            valeur_max = playable_dominos[i].val()
            domino_max = i
    return domino_max #retourne l'indice du domino pouvant etre joué

def minmax(jeu_true, plateau_true:Chain, max_prof, prof,cp, np, j_ia, win_stop, talon):#Elle génère les jeux possibles et retient le domino qui revient le + souvent. pour tt fct recursive, cas de base pour que ca s'arrete
    plateau=Chain(plateau_true.dom_list())
    jeu={}
    for k in jeu_true:
        jeu[k]=[d for d in jeu_true[k]]
    if len(jeu[cp])==1 and can_play(jeu[cp], plateau):
        play_d=jeu[cp][0]
        if play_d.t()[0]==plateau.ex()[1] or play_d.t()[1]==plateau.ex()[1]:
            side='right'
        elif play_d.t()[0]==plateau.ex()[0] or play_d.t()[1]==plateau.ex()[0]:
            side='left'
        if cp==j_ia:
            return (float('-inf'), 0, side)
        else:
            return (float('inf'), 0, side)
    elif max_prof==prof:
        s=0
        for d in jeu[j_ia]:
            s+=d.val()
        return (s, 0, 'right')
    if win_stop==np-1:
        score={}
        for i in range(np):
            s=0
            for d in jeu[i+1]:
                s+=d.val()
            score[i+1]=s
        maxi=1
        for k in score:
            if k==j_ia:
                continue
            if score[k]>score[maxi]:
                maxi=k
        if score[maxi]<=score[j_ia]:
            return (score[maxi]-score[j_ia], 0, 'right')
        else:
            return (float('inf'), 0, 'right')
    else :
        if can_play(jeu[cp], plateau):
            win_stop=0
            playable=playable_dominos(jeu[cp], plateau)
            if cp==j_ia:
                mini=(0, 0, '')
                for cd in range(len(playable)):
                    play_d=playable[cd]
                    right, left=False, False
                    remove(play_d, jeu[cp])
                    if play_d.t()[0]==plateau.ex()[1] :
                        right=True
                        plateau.push(play_d, 'right')
                        score_right = minmax(jeu, plateau, max_prof, prof+1, (cp%np)+1, np, j_ia, win_stop, talon)
                    elif play_d.t()[1] == plateau.ex()[1]:
                        right = True
                        play_d.inv()
                        plateau.push(play_d, 'right')
                        score_right = minmax(jeu, plateau, max_prof, prof+1, (cp%np)+1, np, j_ia, win_stop, talon)
                    if play_d.t()[0]==plateau.ex()[0] :
                        left = True
                        play_d.inv()
                        plateau.push(play_d, 'left')
                        score_left = minmax(jeu, plateau, max_prof, prof+1, (cp%np)+1, np, j_ia, win_stop, talon)
                    elif play_d.t()[1] == plateau.ex()[0]:
                        left = True
                        plateau.push(play_d, 'left')
                        score_left = minmax(jeu, plateau, max_prof, prof+1, (cp%np)+1, np, j_ia, win_stop, talon)
                    if cd==0:
                        if right:
                            mini=(score_right[0],cd,'right')
                            if left and score_left[0]<mini[0]:
                                mini=(score_left[0], cd, 'left')
                        elif left:
                            mini=(score_left[0],cd,'left')
                    else:
                        if right and score_right[0]<mini[0]:
                            mini=(score_right[0], cd, 'right')
                            if left and score_left[0]<mini[0]:
                                mini=(score_left[0], cd, 'left')
                        elif left and score_left[0] < mini[0]:
                                mini = (score_left[0], cd, 'left')
                return mini
            else:
                maxi = (0,0,'')
                for cd in range(len(playable)):
                    play_d = playable[cd]
                    right, left = False, False
                    remove(play_d, jeu[cp])
                    if play_d.t()[0] == plateau.ex()[1]:
                        right = True
                        plateau.push(play_d, 'right')
                        score_right = minmax(jeu, plateau, max_prof, prof + 1, (cp % np) + 1, np, j_ia, win_stop, talon)
                    elif play_d.t()[1] == plateau.ex()[1]:
                        right = True
                        play_d.inv()
                        plateau.push(play_d, 'right')
                        score_right = minmax(jeu, plateau, max_prof, prof + 1, (cp % np) + 1,np, j_ia, win_stop, talon)
                    if play_d.t()[0] == plateau.ex()[0]:
                        left = True
                        play_d.inv()
                        plateau.push(play_d, 'left')
                        score_left = minmax(jeu, plateau, max_prof, prof + 1, (cp % np) + 1, np, j_ia, win_stop, talon)
                    elif play_d.t()[1] == plateau.ex()[0]:
                        left = True
                        plateau.push(play_d, 'left')
                        score_left = minmax(jeu, plateau, max_prof, prof + 1, (cp % np) + 1, np, j_ia, win_stop, talon)
                    if cd == 0:
                        if right:
                            maxi = (score_right[0], cd, 'right')
                            if left and score_left[0] > maxi[0]:
                                maxi = (score_left[0], cd, 'left')
                        elif left:
                            maxi = (score_left[0], cd, 'left')
                    else:
                        if right and score_right[0] > maxi[0]:
                            maxi = (score_right[0], cd, 'right')
                            if left and score_left[0] > maxi[0]:
                                maxi = (score_left[0], cd, 'left')
                        elif left and score_left[0] > maxi[0]:
                            maxi = (score_left[0], cd, 'left')
                return maxi
        else:
            if talon:
                dtemp = talon.pop()
                jeu[cp].append(dtemp)
            else:
                win_stop += 1
            return minmax(jeu, plateau, max_prof, prof+1, cp%np+1, np, j_ia, win_stop, talon)

def choose_minmax(jeu, current_game, j_ia, np, max_prof, win_stop):
    anonymous = anonymous_dominos(jeu[j_ia], current_game)
    tailles_jeux=[]
    for i in range(np):
        if i+1!=j_ia:
            tailles_jeux.append(len(jeu[i+1]))
    guesses=guess_repartition(anonymous, tailles_jeux, 1)
    jeu_guess={}
    jeu_guess[j_ia]=[d for d in jeu[j_ia]]
    results={}
    for r in guesses:
        for i in range(len(r)):
            if i+1<j_ia:
                jeu_guess[i+1]=r[i]
            elif i+1>j_ia:
                jeu_guess[i+1]=r[i-1]
        print(jeu_guess)
        result=minmax(jeu_guess, current_game, max_prof, 0, j_ia, np, j_ia, win_stop, r[len(r)-1])
        k=(result[1], result[2])
        if k in results:
            results[k]+=1
        else:
            results[k]=1
    maxi=0
    for k in results:
        if results[k]>maxi:
            maxi=results[k]
            kmax=k
    return kmax

def play_human() :
    np = int(input("Entrez le nombre de joueurs: "))
    jeu, talon, cp, biggest_domino = distribute(ensemble, np)
    win = False
    win_stop=0 #winstop = True si le talon est vide et le cp peut pas jouer
    current_game: Chain = Chain([biggest_domino]) #chain prend en argument le premier domino de la chaine
    remove(biggest_domino, jeu[cp])
    cp = cp%np + 1

    while not win :
        if can_play(jeu[cp], current_game) : #dans ce cas, le jeu se termine si le joueur n'a plus de domino
            print(f'''c'est au joueur {cp} de jouer.''')
            print(f'''le plateau actuel est {current_game.plateau()}''')
            print(f'''votre jeu actuel est {[d.t() for d in jeu[cp]]}''')
            playable = playable_dominos(jeu[cp], current_game)
            print(f'''vous pouvez jouer les dominos suivants : {[d.t() for d in playable]}''' )
            play_d=int(input("Entrez l'indice du domino à jouer : ")) #input pour pouvoir entrer une question et une reponse de l'user. on precise int psk ca renvoie forcement une chaine de caractere
            playable_left = False
            playable_right = False
            cd = playable[play_d]
            if playable[play_d].t()[0] == current_game.ex()[0] or playable[play_d].t()[1]== current_game.ex()[0] :
                playable_left = True
            if playable[play_d].t()[0] == current_game.ex()[1] or playable[play_d].t()[1] == current_game.ex()[1]:
                playable_right = True
            if playable_left and playable_right :
                side=input("De quel côté du plateau voulez vous le jouer (right or left)? ")
            else:
                side='left' if playable_left else 'right'
            if side=='right':
                if cd.t()[0]!=current_game.ex()[1]:
                    cd.inv()
            else:
                if cd.t()[1]!=current_game.ex()[0]:
                    cd.inv()
            current_game.push(cd, side)
            remove(cd, jeu[cp])
            if not jeu[cp]: #si la liste est vide
                win = True
            else :
                win_stop=0
                cp = cp%np + 1
        else:
            print(f'''le joueur {cp} ne peut pas jouer''')
            if win_stop==np-1:
                win=True
            else:
                if talon:
                    dtemp=talon.pop()
                    jeu[cp].append(dtemp)
                    print(f'''Vous avez pioché le domino : {dtemp.t()}''')
                else:
                    win_stop+=1
                cp = cp%np + 1
    if win_stop==np-1 :
        score= {}
        joueur_min=[]
        score_min=0
        for j in range(np) :
            score[j+1]=0
        for player in score :
            for dom in jeu[player] :
                score[player] += dom.val()
            if player==1:
                score_min = score[1]
                joueur_min = [1]
            else :
                if score[player] < score_min :
                    score_min = score[player]
                    joueur_min = [player]
                elif score[player] == score_min :
                    joueur_min.append(player)
        if len(joueur_min) == 1 :
            print(f'''Le joueur {joueur_min[0]} gagne, avec un score de {score_min} ! Bravo :)''')
        else :
            print(f'''Les joueurs {joueur_min} ont le même score, c'est un match nul. Bravo à tous !''')
    else:
        print(f"Le joueur {cp} a gagné. Bravo !")


def run_stats():
    np = int(input("Combien d'IA voulez-vous voir jouer ?"))  # ex: 2
    joueurs = {}
    max_prof = 1
    for i in range(np):
        difficulte = input(f"Choisissez une IA aléatoire, gloutonne ou minmax pour le joueur {i + 1} : ")
        while not (difficulte in ["aléatoire", "gloutonne", "minmax"]):
            print("ce mode de jeu n'existe pas")
            difficulte = input(f"Choisissez une IA aléatoire, gloutonne ou minmax pour le joueur {i + 1} : ")
        if difficulte == 'minmax':
            max_prof = int(input('entrez une profondeur maximale : '))
        joueurs[i + 1] = difficulte

    nb_parties = int(input("Combien de parties simuler ? "))

    victoires_minmax = 0
    for _ in range(nb_parties):
        jeu, talon, cp, biggest_domino = distribute(ensemble, np)
        win = False
        win_stop = 0
        current_game: Chain = Chain([biggest_domino])
        remove(biggest_domino, jeu[cp])
        gagnant = None

        if not jeu[cp]:
            gagnant = cp
            win = True
        else:
            cp = cp % np + 1

        while not win:
            if can_play(jeu[cp], current_game):
                playable_dom_ia = playable_dominos(jeu[cp], current_game)
                difficulte = joueurs[cp]
                best_side = ''
                if difficulte == 'aléatoire':
                    play_d = choose_alea(playable_dom_ia)
                elif difficulte == 'gloutonne':
                    play_d = choose_naive(playable_dom_ia)
                elif difficulte == 'minmax':
                    result = choose_minmax(jeu, current_game, cp, np, max_prof, win_stop)
                    play_d = result[0]
                    best_side = result[1]

                cd = playable_dom_ia[play_d]
                playable_left = (cd.t()[0] == current_game.ex()[0] or cd.t()[1] == current_game.ex()[0])
                playable_right = (cd.t()[0] == current_game.ex()[1] or cd.t()[1] == current_game.ex()[1])

                if best_side == '':
                    if playable_left and playable_right:
                        side = random.choice(['right', 'left'])
                    else:
                        side = 'left' if playable_left else 'right'
                else:
                    side = best_side

                if side == 'right':
                    if cd.t()[0] != current_game.ex()[1]:
                        cd.inv()
                else:
                    if cd.t()[1] != current_game.ex()[0]:
                        cd.inv()

                current_game.push(cd, side)
                remove(cd, jeu[cp])
                if not jeu[cp]:
                    gagnant = cp
                    win = True
                else:
                    win_stop = 0
                    cp = cp % np + 1
            else:
                if win_stop == np - 1:
                    win = True
                else:
                    if talon:
                        jeu[cp].append(talon.pop())
                    else:
                        win_stop += 1
                    cp = cp % np + 1

        if gagnant is None:
            scores = {j + 1: sum(d.val() for d in jeu[j + 1]) for j in range(np)}
            score_min = min(scores.values())
            min_players = [p for p, sc in scores.items() if sc == score_min]
            if len(min_players) == 1:
                gagnant = min_players[0]

        if gagnant is not None and joueurs[gagnant] == 'minmax':
            victoires_minmax += 1

    print(f"Minimax (profondeur {max_prof}) a gagné {victoires_minmax} / {nb_parties} parties.")



def play_ia():
    np = int(input("Voulez vous jouer contre 1 ou 2 IA ? "))+1
    joueurs={1:'humain'}
    for i in range(np-1):
        difficulte = input(f"Choisissez une IA aléatoire, gloutonne ou minmax pour le joueur {i+2} : ")
        while not (difficulte in ["aléatoire", "gloutonne", "minmax"]):
            print("ce mode de jeu n'existe pas")
            difficulte = input(f"Choisissez une IA aléatoire, gloutonne ou minmax pour le joueur {i+2} : ")
        if difficulte=='minmax':
            max_prof=int(input('entrez une profondeur maximale : '))
        joueurs[i+2]=difficulte
    jeu, talon, cp, biggest_domino = distribute(ensemble, np)
    win = False
    win_stop = 0  # winstop = True si le talon est vide et le cp peut pas jouer
    current_game: Chain = Chain([biggest_domino])  # chain prend en argument le premier domino de la chaine
    remove(biggest_domino, jeu[cp])
    cp = cp % np + 1
    while not win:
        if can_play(jeu[cp], current_game):  # dans ce cas, le jeu se termine si le joueur n'a plus de domino
            if cp == 1 :
                print(f'''c'est au joueur {cp} de jouer.''')
                print(f'''le plateau actuel est {current_game.plateau()}''')
                print(f'''votre jeu actuel est {[d.t() for d in jeu[cp]]}''')
                playable = playable_dominos(jeu[cp], current_game)
                print(f'''vous pouvez jouer les dominos suivants : {[d.t() for d in playable]}''')
                play_d = int(input(
                    "Entrez l'indice du domino à jouer : "))  # input pour pouvoir entrer une question et une reponse de l'user. on precise int psk ca renvoie forcement une chaine de caractere
                playable_left = False
                playable_right = False
                cd = playable[play_d]
                if playable[play_d].t()[0] == current_game.ex()[0] or playable[play_d].t()[1] == current_game.ex()[0]:
                    playable_left = True
                if playable[play_d].t()[0] == current_game.ex()[1] or playable[play_d].t()[1] == current_game.ex()[1]:
                    playable_right = True
                if playable_left and playable_right:
                    side = input("De quel côté du plateau voulez vous le jouer (right or left)? ")
                else:
                    side = 'left' if playable_left else 'right'
            else :
                playable_dom_ia = playable_dominos(jeu[cp], current_game)
                play_d=-1
                difficulte=joueurs[cp]
                best_side=''
                if difficulte == 'aléatoire' :
                    play_d = choose_alea(playable_dom_ia)
                elif difficulte == 'gloutonne' :
                    play_d = choose_naive(playable_dom_ia)
                elif difficulte == 'minmax':
                    result = choose_minmax(jeu, current_game, cp, np, max_prof, win_stop)
                    play_d=result[0]
                    best_side=result[1]
                playable_left = False
                playable_right = False
                cd = playable_dom_ia[play_d]
                print(f"le joueur {cp} a joué le domino {cd.t()}")
                if best_side=='':
                    if playable_dom_ia[play_d].t()[0] == current_game.ex()[0] or playable_dom_ia[play_d].t()[1] == current_game.ex()[
                        0]:
                        playable_left = True
                    if playable_dom_ia[play_d].t()[0] == current_game.ex()[1] or playable_dom_ia[play_d].t()[1] == current_game.ex()[
                        1]:
                        playable_right = True
                    if playable_left and playable_right:
                        sides=['right', 'left']
                        side = sides[random.randint(0,1)]
                    else:
                        side = 'left' if playable_left else 'right'
                else:
                    side=best_side
            if side == 'right':
                if cd.t()[0] != current_game.ex()[1]:
                    cd.inv()
            else:
                if cd.t()[1] != current_game.ex()[0]:
                    cd.inv()
            current_game.push(cd, side)
            remove(cd, jeu[cp])
            if not jeu[cp]:  # si la liste est vide
                win = True
            else:
                win_stop = 0
                cp = cp % np + 1
        else:
            print(f'''le joueur {cp} ne peut pas jouer''')
            if win_stop == np - 1:
                win = True
            else:
                if talon:
                    dtemp = talon.pop()
                    jeu[cp].append(dtemp)
                    if cp==1:
                        print(f'''Vous avez pioché le domino : {dtemp.t()}''')
                else:
                    win_stop += 1
                cp = cp % np + 1
    if win_stop==np-1:
        score = {}
        joueur_min = []
        score_min = 0
        for j in range(np):
            score[j + 1] = 0
        for player in score:
            for dom in jeu[player]:
                score[player] += dom.val()
            if player == 1:
                score_min = score[1]
                joueur_min = [1]
            else:
                if score[player] < score_min:
                    score_min = score[player]
                    joueur_min = [player]
                elif score[player] == score_min:
                    joueur_min.append(player)
        if len(joueur_min) == 1:
            print(f'''Le joueur {joueur_min[0]} gagne, avec un score de {score_min} ! Bravo :)''')
        else:
            print(f'''Les joueurs {joueur_min} ont le même score, c'est un match nul. Bravo à tous !''')
    else:
        print(f"Le joueur {cp} a gagné. Bravo !")

def play_full_ia():
    np = int(input("Combien d'IA voulez-vous voir jouer ?"))
    joueurs = {}
    for i in range(np):
        difficulte = input(f"Choisissez une IA aléatoire, gloutonne ou minmax pour le joueur {i +1} : ")
        while not (difficulte in ["aléatoire", "gloutonne", "minmax"]):
            print("ce mode de jeu n'existe pas")
            difficulte = input(f"Choisissez une IA aléatoire, gloutonne ou minmax pour le joueur {i + 1} : ")
        if difficulte == 'minmax':
            max_prof = int(input('entrez une profondeur maximale : '))
        joueurs[i + 1] = difficulte
    jeu, talon, cp, biggest_domino = distribute(ensemble, np)
    win = False
    win_stop = 0  # winstop = True si le talon est vide et le cp peut pas jouer
    current_game: Chain = Chain([biggest_domino])  # chain prend en argument le premier domino de la chaine
    remove(biggest_domino, jeu[cp])
    cp = cp % np + 1
    while not win:
        if can_play(jeu[cp], current_game):  # dans ce cas, le jeu se termine si le joueur n'a plus de domino
            playable_dom_ia = playable_dominos(jeu[cp], current_game)
            play_d = -1
            difficulte = joueurs[cp]
            best_side = ''
            if difficulte == 'aléatoire':
                play_d = choose_alea(playable_dom_ia)
            elif difficulte == 'gloutonne':
                play_d = choose_naive(playable_dom_ia)
            elif difficulte == 'minmax':
                result = choose_minmax(jeu, current_game, cp, np, max_prof, win_stop)
                play_d = result[0]
                best_side = result[1]
            playable_left = False
            playable_right = False
            cd = playable_dom_ia[play_d]
            print(f"le joueur {cp} a joué le domino {cd.t()}")
            if best_side == '':
                if playable_dom_ia[play_d].t()[0] == current_game.ex()[0] or playable_dom_ia[play_d].t()[1] == \
                        current_game.ex()[
                            0]:
                    playable_left = True
                if playable_dom_ia[play_d].t()[0] == current_game.ex()[1] or playable_dom_ia[play_d].t()[1] == \
                        current_game.ex()[
                            1]:
                    playable_right = True
                if playable_left and playable_right:
                    sides = ['right', 'left']
                    side = sides[random.randint(0, 1)]
                else:
                    side = 'left' if playable_left else 'right'
            else:
                side = best_side
            if side == 'right':
                if cd.t()[0] != current_game.ex()[1]:
                    cd.inv()
            else:
                if cd.t()[1] != current_game.ex()[0]:
                    cd.inv()
            current_game.push(cd, side)
            remove(cd, jeu[cp])
            if not jeu[cp]:  # si la liste est vide
                win = True
            else:
                win_stop = 0
                cp = cp % np + 1
        else:
            print(f'''le joueur {cp} ne peut pas jouer''')
            if win_stop == np - 1:
                win = True
            else:
                if talon:
                    dtemp = talon.pop()
                    jeu[cp].append(dtemp)
                    if cp == 1:
                        print(f'''Vous avez pioché le domino : {dtemp.t()}''')
                else:
                    win_stop += 1
                cp = cp % np + 1
    if win_stop==np-1:
        score = {}
        joueur_min = []
        score_min = 0
        for j in range(np):
            score[j + 1] = 0
        for player in score:
            for dom in jeu[player]:
                score[player] += dom.val()
            if player == 1:
                score_min = score[1]
                joueur_min = [1]
            else:
                if score[player] < score_min:
                    score_min = score[player]
                    joueur_min = [player]
                elif score[player] == score_min:
                    joueur_min.append(player)
        if len(joueur_min) == 1:
            print(f'''Le joueur {joueur_min[0]} gagne, avec un score de {score_min} ! Bravo :)''')
        else:
            print(f'''Les joueurs {joueur_min} ont le même score, c'est un match nul. Bravo à tous !''')
    else:
        print(f"Le joueur {cp} a gagné. Bravo !")

def play():
    style=int(input("Voulez-vous jouer contre un humain, une ia, ou voir plusieurs ia jouer entre elles, ou realiser des stat (enter 0 for human, 1 for AI, 2 for only AI, 3 for stats)? "))
    if style==0:
        play_human()
    elif style==1 :
        play_ia()
    elif style == 3 :
        run_stats()
    else:
        play_full_ia()

if __name__ == "__main__":
    play()
