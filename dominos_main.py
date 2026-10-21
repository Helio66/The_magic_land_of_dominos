import random

class Domino:
    def __init__(self, d:tuple):
        self.d=d #domino sous la forme d'un couple d'entiers
        self.double=(d[0]==d[1]) #test : double ou non ?
    def t(self):
        return self.d
    def db(self):
        return self.double
    def inv(self):
        if not self.double:
            self.d=(self.d[1], self.d[0]) #fct qui inverse les deux positions

class Chain: #jeu en cours
    def __init__(self, d:Domino):
        self.c:list[Domino]=[d]
        self.right=d.t()[1] #valeur du domino tt a droite
        self.left=d.t()[0] #valeur du domino tt a gauche
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

ensemble : list[Domino] = [Domino(i,j) for i in range(7) for j in range(i,7)]

def distribute(jeu) :
    jeu_p1 = []
    jeu_p2 = []
    talon = []
    random.shuffle(jeu)  #melange le jeu a chaque fois
    biggest_domino=jeu[0]
    beggining_p=1
    db=jeu[0].db()
    for i in range(7) :
        jeu_p1.append(jeu[i])
        jeu_p2.append(jeu[7+i])
        talon.append(jeu[14+i])
        if db:
            if jeu[i].db():
                if jeu[i].t()[0]>biggest_domino.t()[0]:
                    biggest_domino=jeu[i]
                    beggining_p=1
            if jeu[i+7].db():
                if jeu[i+7].t()[0] > biggest_domino.t()[0]:
                    biggest_domino = jeu[i+7]
                    beggining_p = 2
        else:
            if jeu[i].db():
                biggest_domino=jeu[i]
                beggining_p=1
                db=True
            if jeu[i+7].db() and db:
                if jeu[i+7].t()[0] > biggest_domino.t()[0]:
                    biggest_domino = jeu[i+7]
                    beggining_p = 2
            if jeu[i+7].db() and not db:
                biggest_domino = jeu[i + 7]
                beggining_p = 2
                db=True
            if not db:
                if jeu[i].t()[0]+jeu[i].t()[1]>biggest_domino.t()[0]+biggest_domino.t()[1]:
                    biggest_domino = jeu[i]
                    beggining_p = 1
                if jeu[i+7].t()[0]+jeu[i+7].t()[1]>biggest_domino.t()[0]+biggest_domino.t()[1]:
                    biggest_domino=jeu[i+7]
                    beggining_p=2
    return jeu_p1, jeu_p2, talon, beggining_p, biggest_domino



def play() :

