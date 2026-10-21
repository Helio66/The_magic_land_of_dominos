class Domino:
    d:tuple # domino
    val:int #la somme des valeurs
    double:bool #on def les attributs
    def inv(self):
        if not self.double:
            self.d=(self.d[1], self.d[0]) #fct qui inverse les deux positions

