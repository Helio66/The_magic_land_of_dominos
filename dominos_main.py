class Domino:
    d:tuple # domino
    val:int #la somme des valeurs
    double:bool #on def les attributs
    def inv(self):
        if not self.double:
            self.d=(self.d[1], self.d[0]) #fct qui inverse les deux positions

class Chain:
    c:list[Domino]
    right=int
    left=int
    def push(self, d:Domino, ex:str):
        if ex=='right':
            self.c.append(d)
            self.right=d.d[1]
        else:
            tempo=[d]
            for dom in self.c:
                tempo.append(dom)
            self.c=[dom for dom in tempo]
            self.left=d.d[0]


