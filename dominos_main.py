class Domino:
    d:tuple # domino
    val:int #la somme des valeurs
    double:bool #on def les attributs
    def inv(self):
        if not self.double:
            self.d=(self.d[1], self.d[0]) #fct qui inverse les deux positions


class Chain: #jeu en cours
    c:list[Domino]
    right=int #valeur du domino tt a droite
    left=int #valeur du domino tt a gauche
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


