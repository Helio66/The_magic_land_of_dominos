class Domino:
    def __init__(self, d:tuple):
        self.d=d #domino sous la forme d'un couple d'entiers
        self.double=(d[0]==d[1]) #test : double ou non ?
    def t(self):
        return self.d
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

dominos : list[Domino] = []
for i in range(7) :
    for j in range(i,7) :
        dominos.append(Domino((i,j)))

print(dominos)
