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
    def __init__(self, d:Domino):
        self.c:list[Domino]=[d]
        self.right=d.t()[1] #valeur du domino tt a droite
        self.left=d.t()[0] #valeur du domino tt a gauche
    def ex(self):
        return self.left, self.right
    def plateau(self):
        return [d.t() for d in self.c]
    def push(self, d:Domino, ex:str): #pour effectuer un nouveau coup
        if ex=='right': #si on peut jouer sur le domino de droite
            self.c.append(d) #on ajt ce domino au jeu
            self.right=d.d[1] #on considère la nvl valeur de droite
        else:
            tempo=[d]
            for dom in self.c:
                tempo.append(dom)
            self.c=[dom for dom in tempo] #on ajoute le domino a gauche
            self.left=d.d[0] #on considere la nvl valeur de gauche

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
                    beginning_p = j
                    db = True
                else:
                    if jeu[j*taille_jeu+i].val() > biggest_domino.val():
                        biggest_domino = jeu[j*taille_jeu+i]
                        beginning_p = j
        talon.append(jeu[np * taille_jeu + i])
    if len(jeu)%(np+1) !=0 :
        for i in range(len(jeu)%(np+1)) :
            talon.append((np+1)*taille_jeu + i)
    return jeu_p, talon, beginning_p, biggest_domino

#print(distribute(ensemble))

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
    return domino_max

def play_human() :
    np = int(input("Entrez le nombre de joueurs: "))
    jeu, talon, cp, biggest_domino = distribute(ensemble, np)
    win = False
    win_stop=0 #winstop = True si le talon est vide et le cp peut pas jouer
    current_game: Chain = Chain(biggest_domino) #chain prend en argument le premier domino de la chaine
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
    if win_stop :
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

def play_ia():
    np = int(input("Voulez vous jouer contre 1 ou 2 IA ? "))+1
    if np == 2 :
        difficulte = input("Choisissez d'affronter une IA aléatoire ou gloutonne : ")
        while not (difficulte in ["aléatoire", "gloutonne"]):
            print("ce mode de jeu n'existe pas")
            difficulte = input("Choisissez entre une IA aléatoire ou gloutonne : ")

    jeu, talon, cp, biggest_domino = distribute(ensemble, np)
    win = False
    win_stop = 0  # winstop = True si le talon est vide et le cp peut pas jouer
    current_game: Chain = Chain(biggest_domino)  # chain prend en argument le premier domino de la chaine
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
                if np == 2 :
                    if difficulte == 'aleatoire' :
                        play_d = choose_alea(playable_dom_ia)
                    elif difficulte == 'gloutonne' :
                        play_d = choose_naive(playable_dom_ia)
                elif np == 3 :
                    if cp == 2:
                        play_d = choose_alea(playable_dom_ia)
                    elif cp == 3 :
                        play_d = choose_naive(playable_dom_ia)
                playable_left = False
                playable_right = False
                cd = playable_dom_ia[play_d]
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
                    print(f'''Vous avez pioché le domino : {dtemp.t()}''')
                else:
                    win_stop += 1
                cp = cp % np + 1
    if win_stop:
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
    style=int(input("Voulez-vous jouer contre un humain ou une ia (enter 0 for human and 1 for AI)? "))
    if style==0:
        play_human()
    else :
        play_ia()

if __name__ == "__main__":
    play()



