"""
partie.py : moteur d'UNE manche de domino à 2, 3 ou 4 joueurs, utilisé par l'interface graphique.

Il réutilise ton code (dominos_main.py) : distribute, Chain, can_play, playable_dominos, remove,
choose_alea, choose_naive, choose_minmax.
Il ne contient AUCUN code Qt : il décrit seulement l'état du jeu et les règles
(poser, piocher, passer, fin de manche). L'interface (dominos_ihm.py) ne fait que l'afficher.

Chaque joueur (numéroté à partir de 1, comme dans dominos_main.py) est soit humain, soit une IA
('aléatoire', 'gloutonne' ou 'minmax'). Tous les mélanges sont permis : plusieurs humains,
un humain contre plusieurs IA, etc. L'IA minmax est limitée à 3 joueurs au plus : avec 4 joueurs,
ton choose_minmax doit énumérer beaucoup trop de répartitions possibles des dominos cachés.

Règles appliquées (les mêmes que dans dominos_main.py) :
  - le joueur qui a le plus grand double (sinon le plus grand domino) ouvre la manche (distribute) ;
  - un joueur qui ne peut pas jouer pioche UN seul domino (s'il reste du talon), puis son tour passe ;
  - si le talon est vide et qu'il ne peut pas jouer, il passe ;
  - la manche se termine quand un joueur n'a plus de domino, ou quand tous les joueurs
    passent à la suite (partie bloquée) ;
  - points marqués par le gagnant : pour chaque adversaire, l'écart entre le total des points restant
    dans sa main et celui du gagnant. Si le gagnant a vidé sa main, c'est donc la somme des points
    restant chez les adversaires (avec 2 joueurs, en cas de blocage : la différence entre les deux totaux) ;
  - en cas de blocage, le plus petit total gagne ; s'il y a égalité pour le plus petit total : manche nulle.
"""
import random

from dominos_main import (ensemble, Chain, distribute, can_play, playable_dominos, remove,
                          choose_alea, choose_naive, choose_minmax)

HUMAIN = 'humain'
MODES_IA = ('aléatoire', 'gloutonne', 'minmax')
NB_JOUEURS_MIN = 2
NB_JOUEURS_MAX = 4
NB_JOUEURS_MAX_MINMAX = 3       # au-delà, le nombre d'hypothèses de choose_minmax explose (mémoire et temps)
PROFONDEUR_DEFAUT = 3


class Partie:
    """État d'une manche. Les joueurs sont numérotés 1, 2, ... comme dans dominos_main.py."""

    def __init__(self, modes, profondeur=PROFONDEUR_DEFAUT):
        """modes : {1: 'humain', 2: 'minmax', 3: 'gloutonne', ...}, un mode par joueur (2 à 4 joueurs).
        profondeur : profondeur max de l'IA minmax. Un entier (valable pour toutes les IA minmax)
                     ou un dictionnaire {joueur: profondeur}."""
        self.np = len(modes)
        if not NB_JOUEURS_MIN <= self.np <= NB_JOUEURS_MAX:
            raise ValueError("il faut entre %d et %d joueurs" % (NB_JOUEURS_MIN, NB_JOUEURS_MAX))
        if sorted(modes) != list(range(1, self.np + 1)):
            raise ValueError("les joueurs doivent être numérotés 1, 2, ..., %d" % self.np)
        for mode in modes.values():
            if mode != HUMAIN and mode not in MODES_IA:
                raise ValueError("mode de joueur inconnu : %r" % (mode,))
        if self.np > NB_JOUEURS_MAX_MINMAX and 'minmax' in modes.values():
            raise ValueError("l'IA minmax n'est disponible que jusqu'à %d joueurs" % NB_JOUEURS_MAX_MINMAX)
        self.modes = dict(modes)
        if isinstance(profondeur, dict):
            self.profondeurs = {j: profondeur.get(j, PROFONDEUR_DEFAUT) for j in self.modes}
        else:
            self.profondeurs = {j: profondeur for j in self.modes}
        # distribute mélange, distribue (9 dominos chacun à 2 joueurs, 7 à 3, 5 à 4) et désigne qui ouvre
        self.jeu, self.talon, ouvreur, premier = distribute(ensemble, self.np)
        self.chaine = Chain([premier])
        remove(premier, self.jeu[ouvreur])
        self.cp = self.suivant(ouvreur)         # joueur courant : celui qui suit l'ouvreur
        self.passes = 0                         # passes consécutives (talon vide)
        self.fini = False
        self.bloquee = False                    # True si la manche finit par un blocage
        self.gagnant = None                     # numéro du gagnant, ou 0 pour une égalité
        self.ex_aequo = []                      # en cas d'égalité : les joueurs à égalité
        self.points = 0                         # points marqués par le gagnant
        self.totaux = {j: 0 for j in self.modes}   # points restant dans chaque main en fin de manche
        self.dernier_cote = None                # côté du dernier domino posé ('left' / 'right')
        # journal des événements : ('ouverture'|'pose'|'pioche'|'passe', joueur, ...)
        self.evenements = [('ouverture', ouvreur, premier.t())]

    # ------------------------------------------------------------------ consultation
    def suivant(self, joueur):
        """Joueur qui joue après `joueur` (même formule que cp % np + 1 dans dominos_main.py)."""
        return joueur % self.np + 1

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
            self.cp = self.suivant(self.cp)

    def piocher(self):
        """Le joueur courant (qui ne peut pas jouer) pioche UN SEUL domino, puis son tour se termine
        (même règle que ton play : il ne rejoue pas, même si le domino pioché est jouable).
        Renvoie le domino pioché."""
        if self.etat_tour() != 'piocher':
            raise ValueError("on ne peut piocher que sans coup possible et avec un talon non vide")
        domino = self.talon.pop()
        self.jeu[self.cp].append(domino)
        self.evenements.append(('pioche', self.cp, domino.t()))
        self.cp = self.suivant(self.cp)          # le tour passe au joueur suivant
        return domino

    def passer(self):
        """Le joueur courant passe son tour (aucun coup possible et talon vide)."""
        if self.etat_tour() != 'passer':
            raise ValueError("on ne peut passer que sans coup possible et avec un talon vide")
        self.passes += 1
        self.evenements.append(('passe', self.cp))
        if self.passes >= self.np:              # tous les joueurs sont bloqués à la suite
            self._terminer(bloquee=True)
        else:
            self.cp = self.suivant(self.cp)

    def _terminer(self, bloquee):
        self.fini = True
        self.bloquee = bloquee
        self.totaux = {j: sum(d.val() for d in self.jeu[j]) for j in self.modes}
        if not bloquee:
            gagnants = [self.cp]                # main vide : total nul, c'est forcément le plus petit
        else:
            plus_petit = min(self.totaux.values())
            gagnants = [j for j in self.modes if self.totaux[j] == plus_petit]
        if len(gagnants) == 1:
            g = gagnants[0]
            self.gagnant = g
            self.ex_aequo = []
            self.points = sum(self.totaux[j] - self.totaux[g] for j in self.modes if j != g)
        else:                                   # égalité pour le plus petit total : manche nulle
            self.gagnant, self.points = 0, 0
            self.ex_aequo = gagnants

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
                i, cote = choose_minmax(self.jeu, self.chaine, self.cp, self.np,
                                        self.profondeurs[self.cp], self.passes)
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
    """Score cumulé sur plusieurs manches (nb_joueurs joueurs, numérotés à partir de 1)."""

    def __init__(self, nb_joueurs=2):
        joueurs = range(1, nb_joueurs + 1)
        self.points = {j: 0 for j in joueurs}
        self.manches = {j: 0 for j in joueurs}
        self.nuls = 0

    def enregistrer(self, partie):
        if partie.gagnant in self.points:
            self.points[partie.gagnant] += partie.points
            self.manches[partie.gagnant] += 1
        else:
            self.nuls += 1
