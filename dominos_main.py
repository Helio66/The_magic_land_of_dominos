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

def distribute(jeu) :
    jeu_p1 = []
    jeu_p2 = []
    talon = []
    random.shuffle(jeu)  #melange le jeu a chaque fois
    biggest_domino=jeu[0]
    beginning_p=1
    db=jeu[0].db()
    for i in range(7) :
        jeu_p1.append(jeu[i])
        jeu_p2.append(jeu[7+i])
        talon.append(jeu[14+i])
        if db:
            if jeu[i].db():
                if jeu[i].t()[0]>biggest_domino.t()[0]:
                    biggest_domino=jeu[i]
                    beginning_p=1
            if jeu[i+7].db():
                if jeu[i+7].t()[0] > biggest_domino.t()[0]:
                    biggest_domino = jeu[i+7]
                    beginning_p = 2
        else:
            if jeu[i].db():
                biggest_domino=jeu[i]
                beginning_p=1
                db=True
            if jeu[i+7].db() and db:
                if jeu[i+7].t()[0] > biggest_domino.t()[0]:
                    biggest_domino = jeu[i+7]
                    beginning_p = 2
            if jeu[i+7].db() and not db:
                biggest_domino = jeu[i + 7]
                beginning_p = 2
                db=True
            if not db:
                if jeu[i].val()>biggest_domino.val():
                    biggest_domino = jeu[i]
                    beginning_p = 1
                if jeu[i+7].val()>biggest_domino.val():
                    biggest_domino=jeu[i+7]
                    beginning_p=2
    return jeu_p1, jeu_p2, talon, beginning_p, biggest_domino

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
        dom = d.t()
        if can_play([d], plateau): #cela va nous dire si on peut jouer le domino d
            playable.append(dom)
    return playable

def remove(d, pile):
    for i in range(len(pile)):
        if pile[i]==d:
            pile[i], pile[len(pile)-1]=pile[len(pile)-1], pile[i] #on echange les pos pour appliquer pop
            pile.pop()
            break #on sort de la boucle pour eviter des recursions inutiles qd on a trv d

def play() :
    jeu_p1, jeu_p2, talon, cp, biggest_domino = distribute(ensemble)
    win = False
    win_stop=False #winstop = True si le talon est vide et le cp peut pas jouer
    jeu={1:jeu_p1, 2:jeu_p2}
    if cp == 1 :
        current_game: Chain = Chain(biggest_domino)#chain prend en argument le premier domino de la chaine
        remove(biggest_domino, jeu_p1)
        cp = 2
    else :
        current_game = Chain(biggest_domino)
        remove(biggest_domino, jeu_p2)
        cp = 1
    while not win :
        if can_play(jeu[cp], current_game) : #dans ce cas, le jeu se termine si le joueur n'a plus de domino
            print(f'''c'est au joueur {cp} de jouer.''')
            print(f'''le plateau actuel est {current_game.plateau()}''')
            print(f'''vous pouvez jouer les dominos suivants : {playable_dominos(jeu[cp], current_game)}''' )
            play_d=int(input("Entrez l'indice du domino à jouer : ")) #input pour pouvoir entrer une question et une reponse de l'user. on precise int psk ca renvoie forcement une chaine de caractere
            side=input("De quel côté du plateau voulez vous le jouer (right or left)? ")
            cd=jeu[cp][play_d]
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
                if win_stop:
                    win_stop=False
                cp = cp%2 + 1
        else:
            print(f'''le joueur {cp} ne peut pas jouer''')
            if win_stop:
                win=True
            else:
                if talon:
                    dtemp=talon.pop()
                    jeu[cp].append(dtemp)
                    print(f'''Vous avez pioché le domino : {dtemp.t()}''')
                else:
                    win_stop=True
                cp = cp%2 + 1
    if win_stop :
        score= {1 : 0, 2 : 0}
        for player in score :
            for dom in jeu[player] :
                score[player] += dom.val()
        if score[1]<score[2]:
            print(f'''Le joueur {1} gagne, avec un score de {score[1]}''')
            print(f'''Le joueur {2} a un score de {score[2]}''')
        elif score[1]>score[2]:
            print(f'''Le joueur {2} gagne, avec un score de {score[2]}''')
            print(f'''Le joueur {1} a un score de {score[1]}''')
        else:
            print(f'''Les deux joueurs ont le même score, c'est un match nul. Bravo à tous les deux !''')
    else:
        print(f"{cp} a gagné. Bravo !")

play()



