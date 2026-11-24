"""
partie.py : moteur d'UNE manche de domino à 2 joueurs, utilisé par l'interface graphique.

Il réutilise ton code (domino.py) : distribute, Chain, can_play, playable_dominos, remove,
choose_alea, choose_naive, choose_minmax.
Il ne contient AUCUN code Qt : il décrit seulement l'état du jeu et les règles
(poser, piocher, passer, fin de manche). L'interface (domino_gui.py) ne fait que l'afficher.

Règles appliquées :
  - le joueur qui a le plus grand double (sinon le plus grand domino) ouvre la manche (distribute) ;
  - un joueur qui ne peut pas jouer pioche UN seul domino (s'il reste du talon), puis son tour passe ;
  - si le talon est vide et qu'il ne peut pas jouer, il passe ;
  - la manche se termine quand un joueur n'a plus de domino, ou quand les deux joueurs
    passent à la suite (partie bloquée) ;
  - le gagnant marque les points restants dans la main de l'adversaire
    (en cas de blocage : la différence entre les deux totaux, le plus petit total gagne).
"""
import random

from dominos_main import (ensemble, Chain, distribute, can_play, playable_dominos, remove,
                    choose_alea, choose_naive, choose_minmax)

HUMAIN = 'humain'
MODES_IA = ('aléatoire', 'gloutonne', 'minmax')


class Partie:
    """État d'une manche. Les joueurs sont numérotés 1 et 2, comme dans domino.py."""

    def __init__(self, modes, profondeur=3):
        """modes : {1: 'humain', 2: 'humain' | 'aléatoire' | 'gloutonne' | 'minmax'}."""
        self.modes = modes
        self.profondeur = profondeur            # profondeur max de l'IA minmax
        # distribute mélange, distribue (9 dominos chacun avec ta version) et désigne qui ouvre
        self.jeu, self.talon, ouvreur, premier = distribute(ensemble, 2)
        self.chaine = Chain([premier])
        remove(premier, self.jeu[ouvreur])
        self.cp = ouvreur % 2 + 1               # joueur courant : celui qui n'a pas ouvert
        self.passes = 0                         # passes consécutives (talon vide)
        self.fini = False
        self.bloquee = False                    # True si la manche finit par un blocage
        self.gagnant = None                     # 1, 2, ou 0 pour une égalité
        self.points = 0                         # points marqués par le gagnant
        self.totaux = {1: 0, 2: 0}              # points restant dans chaque main en fin de manche
        self.dernier_cote = None                # côté du dernier domino posé ('left' / 'right')
        # journal des événements : ('ouverture'|'pose'|'pioche'|'passe', joueur, ...)
        self.evenements = [('ouverture', ouvreur, premier.t())]

    # ------------------------------------------------------------------ consultation
    def est_ia(self, joueur):
        return self.modes[joueur] != HUMAIN

    def etat_tour(self):
        """Ce que doit faire le joueur courant : 'jouer', 'piocher', 'passer' ou 'fini'."""
        if self.fini:
            return 'fini'
        if can_play(self.jeu[self.cp], self.chaine):
            return 'jouer'
        if self.talon:
            return 'piocher'
        return 'passer'

    def jouables(self):
        """Dominos du joueur courant qui peuvent être posés."""
        return playable_dominos(self.jeu[self.cp], self.chaine)

    def cotes_legaux(self, domino):
        """Côtés ('left' et/ou 'right') où ce domino peut être posé."""
        gauche, droite = self.chaine.ex()
        valeurs = domino.t()
        cotes = []
        if gauche in valeurs:
            cotes.append('left')
        if droite in valeurs:
            cotes.append('right')
        return cotes

    # ------------------------------------------------------------------ actions
    def poser(self, domino, cote):
        """Pose un domino de la main du joueur courant. Lève ValueError si le coup est illégal."""
        if self.fini:
            raise ValueError("la manche est terminée")
        if domino not in self.jeu[self.cp]:
            raise ValueError("ce domino n'est pas dans la main du joueur courant")
        if cote not in self.cotes_legaux(domino):
            raise ValueError("coup illégal : ce domino ne se pose pas de ce côté")
        # on retourne le domino pour que le bon chiffre touche la chaîne (même logique que ton play)
        if cote == 'right':
            if domino.t()[0] != self.chaine.ex()[1]:
                domino.inv()
        else:
            if domino.t()[1] != self.chaine.ex()[0]:
                domino.inv()
        self.chaine.push(domino, cote)
        remove(domino, self.jeu[self.cp])
        self.dernier_cote = cote
        self.passes = 0
        self.evenements.append(('pose', self.cp, domino.t(), cote))
        if not self.jeu[self.cp]:               # main vide : le joueur courant gagne la manche
            self._terminer(bloquee=False)
        else:
            self.cp = self.cp % 2 + 1

    def piocher(self):
        """Le joueur courant (qui ne peut pas jouer) pioche UN SEUL domino, puis son tour se termine
        (même règle que ton play : il ne rejoue pas, même si le domino pioché est jouable).
        Renvoie le domino pioché."""
        if self.etat_tour() != 'piocher':
            raise ValueError("on ne peut piocher que sans coup possible et avec un talon non vide")
        domino = self.talon.pop()
        self.jeu[self.cp].append(domino)
        self.evenements.append(('pioche', self.cp, domino.t()))
        self.cp = self.cp % 2 + 1                # le tour passe à l'autre joueur
        return domino

    def passer(self):
        """Le joueur courant passe son tour (aucun coup possible et talon vide)."""
        if self.etat_tour() != 'passer':
            raise ValueError("on ne peut passer que sans coup possible et avec un talon vide")
        self.passes += 1
        self.evenements.append(('passe', self.cp))
        if self.passes >= 2:                    # les deux joueurs sont bloqués à la suite
            self._terminer(bloquee=True)
        else:
            self.cp = self.cp % 2 + 1

    def _terminer(self, bloquee):
        self.fini = True
        self.bloquee = bloquee
        self.totaux = {j: sum(d.val() for d in self.jeu[j]) for j in (1, 2)}
        if not bloquee:
            self.gagnant = self.cp
            self.points = self.totaux[3 - self.cp]
        elif self.totaux[1] < self.totaux[2]:
            self.gagnant, self.points = 1, self.totaux[2] - self.totaux[1]
        elif self.totaux[2] < self.totaux[1]:
            self.gagnant, self.points = 2, self.totaux[1] - self.totaux[2]
        else:
            self.gagnant, self.points = 0, 0

    # ------------------------------------------------------------------ IA
    def choisir_coup_ia(self):
        """Choisit le coup de l'IA courante. Renvoie (domino, côté). Ne modifie pas la partie.
        (peut être long avec minmax : l'interface l'appelle dans un thread)"""
        jouables = self.jouables()
        mode = self.modes[self.cp]
        cote = None
        if mode == 'aléatoire':
            i = choose_alea(jouables)
        elif mode == 'gloutonne':
            i = choose_naive(jouables)
        else:                                   # 'minmax' : ton choose_minmax, qui renvoie (indice, côté)
            try:
                i, cote = choose_minmax(self.jeu, self.chaine, self.cp, 2, self.profondeur, self.passes)
                if not 0 <= i < len(jouables):
                    raise IndexError("indice de domino hors liste")
            except Exception as erreur:         # garde-fou : on ne bloque jamais la partie
                print("minmax a échoué (%r) : coup glouton à la place" % (erreur,))
                i, cote = choose_naive(jouables), None
        domino = jouables[i]
        cotes = self.cotes_legaux(domino)
        if cote not in cotes:                   # côté absent ou invalide : au hasard parmi les côtés légaux
            cote = random.choice(cotes)
        return domino, cote


class Score:
    """Score cumulé sur plusieurs manches."""

    def __init__(self):
        self.points = {1: 0, 2: 0}
        self.manches = {1: 0, 2: 0}
        self.nuls = 0

    def enregistrer(self, partie):
        if partie.gagnant in (1, 2):
            self.points[partie.gagnant] += partie.points
            self.manches[partie.gagnant] += 1
        else:
            self.nuls += 1
