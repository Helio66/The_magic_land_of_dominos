class Domino:
    d:tuple
    val:int
    double:bool
    def inv(self):
        if not self.double:
            self.d=(self.d[1], self.d[0])