"""
dominos_ihm.py : interface graphique PyQt (PyQt6 ou PyQt5) du jeu de domino.

Lancer :   python dominos_ihm.py
Dans le même dossier : dominos_main.py (ton jeu) et partie.py (moteur d'une manche).

Fonctionnalités : partie à 2, 3 ou 4 joueurs. Chaque joueur est au choix humain, IA aléatoire, IA gloutonne
ou IA minmax (avec sa profondeur) : plusieurs humains sur le même écran (main masquée entre deux tours),
un humain contre plusieurs IA, ou n'importe quel mélange. Affichage de la chaîne, de la main du joueur
courant, des mains cachées des adversaires, du talon et du score ; dominos jouables en évidence, choix de
l'extrémité ; boutons piocher / passer ; fin de manche ; nouvelle manche ou nouvelle partie sans relancer
le programme.
"""
import random
import sys
import threading

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except ImportError:                      # pas de PyQt6 : on essaie PyQt5
    from PyQt5 import QtCore, QtGui, QtWidgets

from partie import (Partie, Score, HUMAIN, NB_JOUEURS_MIN, NB_JOUEURS_MAX,
                    NB_JOUEURS_MAX_MINMAX)

Qt = QtCore.Qt


def _enum(classe, groupe, nom):
    """Récupère une constante Qt, qu'on soit en PyQt6 (Qt.AlignmentFlag.AlignCenter)
    ou en PyQt5 (Qt.AlignCenter)."""
    conteneur = getattr(classe, groupe, None)
    if conteneur is not None and hasattr(conteneur, nom):
        return getattr(conteneur, nom)
    return getattr(classe, nom)


ALIGN_CENTRE = _enum(Qt, "AlignmentFlag", "AlignCenter")
# QPainter.drawText attend un entier pour l'alignement (en PyQt6 l'énumération a un .value)
ALIGN_CENTRE_INT = getattr(ALIGN_CENTRE, "value", ALIGN_CENTRE)
STYLED_BACKGROUND = _enum(Qt, "WidgetAttribute", "WA_StyledBackground")
BOUTON_GAUCHE = _enum(Qt, "MouseButton", "LeftButton")
PAS_DE_STYLO = _enum(Qt, "PenStyle", "NoPen")
TIRETS = _enum(Qt, "PenStyle", "DashLine")
PAS_DE_PINCEAU = _enum(Qt, "BrushStyle", "NoBrush")
SANS_BARRE = _enum(Qt, "ScrollBarPolicy", "ScrollBarAlwaysOff")
ANTIALIAS = _enum(QtGui.QPainter, "RenderHint", "Antialiasing")

# ----------------------------------------------------------------------------- couleurs
IVOIRE = "#f7f1e1"
BORD = "#2b2b2b"
SEPARATEUR = "#8a8271"
POINTS = "#1c1c1c"
DOS = "#2a4d8f"
DOS_CLAIR = "#7f9bd3"
FEUTRE = "#1f5c3d"
VERT = "#35c26b"
OR = "#f2b01e"

# position des points dans la moitié d'un domino (fractions du côté de la moitié)
_G, _C, _H = 0.25, 0.5, 0.75
POINTS_PAR_VALEUR = {
    0: [],
    1: [(_C, _C)],
    2: [(_G, _G), (_H, _H)],
    3: [(_G, _G), (_C, _C), (_H, _H)],
    4: [(_G, _G), (_H, _G), (_G, _H), (_H, _H)],
    5: [(_G, _G), (_H, _G), (_C, _C), (_G, _H), (_H, _H)],
    6: [(_G, _G), (_H, _G), (_G, _C), (_H, _C), (_G, _H), (_H, _H)],
}

STYLE = """
QWidget { color: #222222; font-size: 14px; }
QMainWindow, QWidget#page { background: #f3f1ea; }
QGroupBox { border: 1px solid #c9c5b8; border-radius: 8px; margin-top: 12px; padding: 10px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
QLineEdit, QSpinBox, QComboBox { background: white; border: 1px solid #b9b5a8; border-radius: 5px; padding: 4px 6px; }
QPushButton { background: #e8e6df; border: 1px solid #b9b5a8; border-radius: 6px; padding: 8px 16px; }
QPushButton:hover { background: #dedbd1; }
QPushButton:disabled { color: #a3a095; background: #eeece6; border-color: #d8d5ca; }
QPushButton#principal { background: #2e9d57; color: white; border: none; font-weight: bold; }
QPushButton#principal:hover { background: #28884b; }
QPushButton#alerte:enabled { background: #f2b01e; color: #1d1d1d; font-weight: bold; border: 1px solid #b27d0c; }
QLabel#titre { font-size: 34px; font-weight: bold; }
QLabel#tour { font-size: 20px; font-weight: bold; }
QLabel#talon { font-size: 16px; font-weight: bold; padding: 0 12px; }
QLabel#score { color: #555555; }
QLabel#aide { color: #555555; }
QLabel#erreur { color: #b3261e; font-weight: bold; }
QFrame#bandeau { background: #fff3c9; border: 2px solid #f2b01e; border-radius: 10px; }
QLabel#fin { font-size: 17px; font-weight: bold; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QComboBox QAbstractItemView { background: white; color: #222222; selection-background-color: #cfe8d7; selection-color: #222222; }
"""


def palette_claire():
    """Palette claire imposée : l'interface reste lisible même si le thème du système est sombre."""
    palette = QtGui.QPalette()
    for role, couleur in (("Window", "#f3f1ea"), ("WindowText", "#222222"), ("Base", "#ffffff"),
                          ("AlternateBase", "#f3f1ea"), ("Text", "#222222"), ("Button", "#e8e6df"),
                          ("ButtonText", "#222222"), ("Highlight", "#2e9d57"), ("HighlightedText", "#ffffff"),
                          ("ToolTipBase", "#ffffdc"), ("ToolTipText", "#222222")):
        palette.setColor(_enum(QtGui.QPalette, "ColorRole", role), QtGui.QColor(couleur))
    return palette


def _pos(evenement):
    """Position (x, y) d'un clic de souris, en PyQt5 comme en PyQt6."""
    p = evenement.position() if hasattr(evenement, "position") else evenement.pos()
    return p.x(), p.y()


# ----------------------------------------------------------------------------- dessin
def disposer(largeur, tailles, marge=10, gap=8, hmin=0):
    """Range des rectangles (largeur, hauteur) de gauche à droite avec retour à la ligne.
    Renvoie (liste de (x, y, w, h), hauteur totale). Les éléments d'une ligne sont centrés
    verticalement. Fonction pure : elle sert au dessin ET au repérage des clics."""
    lignes, ligne, x = [], [], marge
    for i, (w, h) in enumerate(tailles):
        if ligne and x + w > largeur - marge:      # plus de place : on passe à la ligne
            lignes.append(ligne)
            ligne, x = [], marge
        ligne.append((i, x, w, h))
        x += w + gap
    if ligne:
        lignes.append(ligne)
    resultat = [None] * len(tailles)
    y = marge
    for ligne in lignes:
        hauteur_ligne = max([hmin] + [h for (_, _, _, h) in ligne])
        for i, x, w, h in ligne:
            resultat[i] = (x, y + (hauteur_ligne - h) / 2, w, h)
        y += hauteur_ligne + gap
    total = (y - gap + marge) if lignes else 2 * marge
    return resultat, total


def dessiner_domino(p, x, y, w, h, a, b, dos=False, opacite=1.0, contour=None):
    """Dessine un domino dans le rectangle (x, y, w, h). Horizontal si w > h : a à gauche et b
    à droite. Vertical si h > w : a en haut et b en bas. dos=True : face cachée."""
    p.save()
    p.setOpacity(opacite)
    cote = min(w, h)
    rayon = cote * 0.18
    rect = QtCore.QRectF(x, y, w, h)
    p.setPen(QtGui.QPen(QtGui.QColor(BORD), 1.5))
    p.setBrush(QtGui.QBrush(QtGui.QColor(DOS if dos else IVOIRE)))
    p.drawRoundedRect(rect, rayon, rayon)
    vertical = h > w
    if dos:
        p.setPen(QtGui.QPen(QtGui.QColor(DOS_CLAIR), 1.2))
        if vertical:
            p.drawLine(QtCore.QPointF(x + cote * 0.15, y + h / 2), QtCore.QPointF(x + w - cote * 0.15, y + h / 2))
        else:
            p.drawLine(QtCore.QPointF(x + w / 2, y + cote * 0.15), QtCore.QPointF(x + w / 2, y + h - cote * 0.15))
    else:
        p.setPen(QtGui.QPen(QtGui.QColor(SEPARATEUR), 1.5))      # trait qui sépare les deux moitiés
        if vertical:
            p.drawLine(QtCore.QPointF(x + cote * 0.12, y + h / 2), QtCore.QPointF(x + w - cote * 0.12, y + h / 2))
        else:
            p.drawLine(QtCore.QPointF(x + w / 2, y + cote * 0.12), QtCore.QPointF(x + w / 2, y + h - cote * 0.12))
        p.setPen(PAS_DE_STYLO)
        p.setBrush(QtGui.QBrush(QtGui.QColor(POINTS)))
        rayon_point = cote * 0.08
        for k, valeur in enumerate((a, b)):
            sx, sy = (x, y + k * h / 2) if vertical else (x + k * w / 2, y)
            for fx, fy in POINTS_PAR_VALEUR[valeur]:
                p.drawEllipse(QtCore.QPointF(sx + fx * cote, sy + fy * cote), rayon_point, rayon_point)
    if contour:
        p.setPen(QtGui.QPen(QtGui.QColor(contour), 3))
        p.setBrush(PAS_DE_PINCEAU)
        p.drawRoundedRect(rect, rayon, rayon)
    p.restore()


# ----------------------------------------------------------------------------- widgets
class MainWidget(QtWidgets.QWidget):
    """Une rangée de dominos debout : la main d'un joueur (cliquable)."""
    clique = QtCore.pyqtSignal(int)          # indice du domino cliqué
    double_clique = QtCore.pyqtSignal(int)
    revelee = QtCore.pyqtSignal()            # clic sur une main masquée

    def __init__(self, S=44, parent=None):
        super().__init__(parent)
        self.S = S                           # largeur d'un domino (la hauteur vaut 2 * S)
        self.tuiles = []                     # [(a, b), ...]
        self.jouables = None                 # indices jouables (None : pas de mise en évidence)
        self.selection = None                # indice du domino sélectionné
        self.dos = False                     # True : dominos face cachée
        self.masquee = False                 # True : main cachée, cliquer pour l'afficher
        self.texte_masque = ""
        self._rects = []
        self.setMinimumHeight(2 * S + 28)

    def set_etat(self, tuiles, jouables=None, selection=None, dos=False, masquee=False, texte_masque=""):
        self.tuiles = list(tuiles)
        self.jouables = jouables
        self.selection = selection
        self.dos = dos
        self.masquee = masquee
        self.texte_masque = texte_masque
        self._recalculer()
        self.update()

    def _recalculer(self):
        S = self.S
        self._rects, h = disposer(self.width(), [(S, 2 * S)] * len(self.tuiles), marge=14, gap=10)
        h = max(int(h), 2 * S + 28)
        if h != self.minimumHeight():
            self.setMinimumHeight(h)

    def resizeEvent(self, evenement):
        self._recalculer()
        super().resizeEvent(evenement)

    def paintEvent(self, evenement):
        p = QtGui.QPainter(self)
        p.setRenderHint(ANTIALIAS)
        for i, ((a, b), (x, y, w, h)) in enumerate(zip(self.tuiles, self._rects)):
            if self.dos or self.masquee:
                dessiner_domino(p, x, y, w, h, 0, 0, dos=True)
                continue
            opacite, contour = 1.0, None
            if self.jouables is not None:
                if i in self.jouables:
                    contour = VERT           # coup légal : cadre vert
                else:
                    opacite = 0.45           # coup impossible : domino grisé
            if i == self.selection:
                y -= 12                      # le domino sélectionné se soulève
                contour = OR
            dessiner_domino(p, x, y, w, h, a, b, opacite=opacite, contour=contour)
        if self.masquee and self.texte_masque:
            bande = QtCore.QRectF(0, self.height() / 2 - 24, self.width(), 48)
            p.setPen(PAS_DE_STYLO)
            p.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 175)))
            p.drawRect(bande)
            police = QtGui.QFont(self.font())
            police.setBold(True)
            police.setPointSize(13)
            p.setFont(police)
            p.setPen(QtGui.QColor("white"))
            p.drawText(bande, ALIGN_CENTRE_INT, self.texte_masque)
        p.end()

    def _indice_en(self, px, py):
        for i, (x, y, w, h) in enumerate(self._rects):
            if x <= px <= x + w and y - 12 <= py <= y + h:
                return i
        return None

    def mousePressEvent(self, evenement):
        if evenement.button() != BOUTON_GAUCHE:
            return
        if self.masquee:
            self.revelee.emit()
            return
        i = self._indice_en(*_pos(evenement))
        if i is not None:
            self.clique.emit(i)

    def mouseDoubleClickEvent(self, evenement):
        if evenement.button() != BOUTON_GAUCHE or self.masquee:
            return
        i = self._indice_en(*_pos(evenement))
        if i is not None:
            self.double_clique.emit(i)


class ChaineWidget(QtWidgets.QWidget):
    """La chaîne de dominos posés, sur un tapis vert. Aux deux bouts, une zone cliquable
    ('left' / 'right') s'allume quand le domino sélectionné peut y être posé."""
    zone_cliquee = QtCore.pyqtSignal(str)

    def __init__(self, S=30, parent=None):
        super().__init__(parent)
        self.S = S
        self.tuiles = []
        self.extremites = (None, None)
        self.zones_actives = set()
        self.dernier = None                  # indice du dernier domino posé (entouré en or)
        self._items = []
        self._rects = []
        self.setMinimumHeight(2 * S + 24)

    def set_etat(self, tuiles, extremites, zones_actives, dernier=None):
        self.tuiles = list(tuiles)
        self.extremites = extremites
        self.zones_actives = set(zones_actives)
        self.dernier = dernier
        self._recalculer()
        self.update()

    def _recalculer(self):
        S = self.S
        L = 2 * S
        self._items = [('zone', 'left')] + [('tuile', i) for i in range(len(self.tuiles))] + [('zone', 'right')]
        tailles = []
        for genre, ref in self._items:
            if genre == 'zone':
                tailles.append((L, S))
            else:
                a, b = self.tuiles[ref]
                tailles.append((S, L) if a == b else (L, S))      # un double se pose en travers
        self._rects, h = disposer(self.width(), tailles, marge=12, gap=6, hmin=L)
        h = max(int(h), L + 24)
        if h != self.minimumHeight():
            self.setMinimumHeight(h)

    def resizeEvent(self, evenement):
        self._recalculer()
        super().resizeEvent(evenement)

    def paintEvent(self, evenement):
        p = QtGui.QPainter(self)
        p.setRenderHint(ANTIALIAS)
        p.setPen(PAS_DE_STYLO)
        p.setBrush(QtGui.QBrush(QtGui.QColor(FEUTRE)))
        p.drawRoundedRect(QtCore.QRectF(0, 0, self.width(), self.height()), 12, 12)
        police = QtGui.QFont(self.font())
        police.setBold(True)
        police.setPointSize(13)
        for (genre, ref), (x, y, w, h) in zip(self._items, self._rects):
            if genre == 'tuile':
                a, b = self.tuiles[ref]
                dessiner_domino(p, x, y, w, h, a, b, contour=OR if ref == self.dernier else None)
                continue
            actif = ref in self.zones_actives
            rect = QtCore.QRectF(x, y, w, h)
            p.save()
            p.setOpacity(1.0 if actif else 0.18)
            couleur = QtGui.QColor(VERT if actif else "#ffffff")
            fond = QtGui.QColor(couleur)
            fond.setAlpha(70 if actif else 0)
            stylo = QtGui.QPen(couleur, 2)
            stylo.setStyle(TIRETS)
            p.setPen(stylo)
            p.setBrush(QtGui.QBrush(fond))
            p.drawRoundedRect(rect, 8, 8)
            if actif:
                valeur = self.extremites[0] if ref == 'left' else self.extremites[1]
                texte = "◀  %s" % valeur if ref == 'left' else "%s  ▶" % valeur
                p.setFont(police)
                p.setPen(QtGui.QColor("white"))
                p.drawText(rect, ALIGN_CENTRE_INT, texte)
            p.restore()
        p.end()

    def mousePressEvent(self, evenement):
        if evenement.button() != BOUTON_GAUCHE:
            return
        px, py = _pos(evenement)
        for (genre, ref), (x, y, w, h) in zip(self._items, self._rects):
            if genre == 'zone' and ref in self.zones_actives and x <= px <= x + w and y <= py <= y + h:
                self.zone_cliquee.emit(ref)
                return


# ----------------------------------------------------------------------------- écran de réglages
# (texte affiché, code du mode) pour le type de chaque joueur
TYPES_JOUEUR = (
    ("Humain", HUMAIN),
    ("IA aléatoire (joue au hasard)", "aléatoire"),
    ("IA gloutonne (pose le domino le plus lourd)", "gloutonne"),
    ("IA minmax (explore les coups possibles)", "minmax"),
)
TYPES_PAR_DEFAUT = (HUMAIN, "minmax", "gloutonne", "aléatoire")     # pour les joueurs 1 à 4
PROF_REGLAGE_DEFAUT = 3


def nom_auto(code, prof, numero):
    """Nom proposé quand le champ « nom » est laissé vide."""
    if code == HUMAIN:
        return "Joueur %d" % numero
    if code == "minmax":
        return "IA minmax (prof. %d)" % prof
    return "IA %s" % code


class PageReglages(QtWidgets.QWidget):
    """Premier écran : nombre de joueurs (2 à 4) et, pour chacun, son nom et son type
    (humain ou IA aléatoire / gloutonne / minmax). Tous les mélanges sont possibles."""
    demarrer = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self.setAttribute(STYLED_BACKGROUND, True)
        W = QtWidgets
        racine = W.QVBoxLayout(self)
        racine.setContentsMargins(40, 24, 40, 24)
        titre = W.QLabel("Domino")
        titre.setObjectName("titre")
        titre.setAlignment(ALIGN_CENTRE)
        racine.addWidget(titre)

        # --- nombre de joueurs
        boite_nb = W.QGroupBox("Table")
        ln = W.QHBoxLayout(boite_nb)
        ln.addWidget(W.QLabel("Nombre de joueurs :"))
        self.sp_nb = W.QSpinBox()
        self.sp_nb.setRange(NB_JOUEURS_MIN, NB_JOUEURS_MAX)
        self.sp_nb.setValue(2)
        ln.addWidget(self.sp_nb)
        ln.addStretch(1)
        racine.addWidget(boite_nb)

        # --- un siège par joueur : nom, type, profondeur minmax
        boite_j = W.QGroupBox("Joueurs")
        grille = W.QGridLayout(boite_j)
        grille.setHorizontalSpacing(10)
        grille.addWidget(W.QLabel("Nom (facultatif)"), 0, 1)
        grille.addWidget(W.QLabel("Type"), 0, 2)
        grille.addWidget(W.QLabel("Profondeur minmax"), 0, 3)
        self.sieges = []                     # [(étiquette, nom, type, profondeur)] pour les joueurs 1 à 4
        for k in range(NB_JOUEURS_MAX):
            etiquette = W.QLabel("Joueur %d :" % (k + 1))
            nom = W.QLineEdit()
            type_ = W.QComboBox()
            for texte, code in TYPES_JOUEUR:
                type_.addItem(texte, code)
            type_.setCurrentIndex([code for _, code in TYPES_JOUEUR].index(TYPES_PAR_DEFAUT[k]))
            prof = W.QSpinBox()
            prof.setRange(1, 8)
            prof.setValue(PROF_REGLAGE_DEFAUT)
            for colonne, widget in enumerate((etiquette, nom, type_, prof)):
                grille.addWidget(widget, k + 1, colonne)
            grille.setColumnStretch(1, 1)
            self.sieges.append((etiquette, nom, type_, prof))
            nom.textChanged.connect(self._maj)
            type_.currentIndexChanged.connect(self._maj)
            prof.valueChanged.connect(self._maj)
        self.chk_cacher = W.QCheckBox("Masquer la main entre deux tours (plusieurs humains sur le même écran)")
        self.chk_cacher.setChecked(True)
        grille.addWidget(self.chk_cacher, NB_JOUEURS_MAX + 1, 0, 1, 4)
        racine.addWidget(boite_j)

        # --- remarques
        self.lbl_info = W.QLabel()
        self.lbl_info.setObjectName("aide")
        self.lbl_info.setWordWrap(True)
        racine.addWidget(self.lbl_info)
        self.lbl_erreur = W.QLabel("Il faut au moins un joueur humain.")
        self.lbl_erreur.setObjectName("erreur")
        racine.addWidget(self.lbl_erreur)

        racine.addStretch(1)
        self.btn = W.QPushButton("Commencer la partie")
        self.btn.setObjectName("principal")
        racine.addWidget(self.btn)

        self.sp_nb.valueChanged.connect(self._maj)
        self.btn.clicked.connect(self._valider)
        self._maj()

    # ---------------------------------------------------------------- cohérence des réglages
    def _maj(self, *_):
        """Active seulement les réglages qui ont un sens pour la configuration choisie."""
        nb = self.sp_nb.value()
        minmax_permis = nb <= NB_JOUEURS_MAX_MINMAX
        nb_humains, nb_minmax = 0, 0
        for k, (etiquette, nom, type_, prof) in enumerate(self.sieges):
            present = k < nb
            for widget in (etiquette, nom, type_, prof):
                widget.setVisible(present)
            # minmax indisponible à 4 joueurs : on grise l'option (et on bascule en gloutonne si besoin)
            indice_minmax = type_.findData("minmax")
            type_.model().item(indice_minmax).setEnabled(minmax_permis)
            if not minmax_permis and type_.currentData() == "minmax":
                type_.blockSignals(True)
                type_.setCurrentIndex(type_.findData("gloutonne"))
                type_.blockSignals(False)
            code = type_.currentData()
            if present:
                nb_humains += code == HUMAIN
                nb_minmax += code == "minmax"
            prof.setEnabled(code == "minmax")
            nom.setPlaceholderText(nom_auto(code, prof.value(), k + 1))
        self.chk_cacher.setEnabled(nb_humains >= 2)
        self.btn.setEnabled(nb_humains >= 1)
        self.lbl_erreur.setVisible(nb_humains == 0)
        if not minmax_permis:
            info = ("Avec %d joueurs, l'IA minmax n'est pas disponible (trop de répartitions possibles "
                    "des dominos cachés à explorer) : choisissez une IA aléatoire ou gloutonne." % nb)
        elif nb_minmax and nb == NB_JOUEURS_MAX_MINMAX:
            info = ("Avec %d joueurs, l'IA minmax peut mettre plusieurs secondes par coup (surtout en début "
                    "de manche), d'autant plus que sa profondeur est grande." % nb)
        else:
            info = ""
        self.lbl_info.setText(info)
        self.lbl_info.setVisible(bool(info))

    def _valider(self):
        nb = self.sp_nb.value()
        modes, profs, bruts = {}, {}, {}
        for k in range(nb):
            _, nom, type_, prof = self.sieges[k]
            numero = k + 1
            modes[numero] = type_.currentData()
            profs[numero] = prof.value()
            bruts[numero] = nom.text().strip() or nom_auto(modes[numero], profs[numero], numero)
        # deux joueurs ne doivent pas porter le même nom : on ajoute leur numéro
        noms = {j: (n if list(bruts.values()).count(n) == 1 else "%s (joueur %d)" % (n, j))
                for j, n in bruts.items()}
        self.demarrer.emit({
            'modes': modes,                  # {1: 'humain', 2: 'minmax', ...}
            'profs': profs,                  # profondeur minmax de chaque joueur
            'noms': noms,
            'cacher': self.chk_cacher.isChecked() and self.chk_cacher.isEnabled(),
        })


# ----------------------------------------------------------------------------- écran de jeu
class _PontIA(QtCore.QObject):
    """Sert à renvoyer le résultat du thread de l'IA vers le thread de l'interface."""
    termine = QtCore.pyqtSignal(int, object)       # (jeton de la manche, (domino, côté) ou None)


class PageJeu(QtWidgets.QWidget):
    """Écran de jeu : relie le moteur (Partie) aux widgets. Gère 2 à 4 joueurs, humains et/ou IA."""
    retour_reglages = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self.setAttribute(STYLED_BACKGROUND, True)
        self.partie = None
        self.score = Score()
        self.reglages = {'modes': {1: HUMAIN, 2: HUMAIN}, 'profs': {}, 'cacher': False,
                         'noms': {1: "Joueur 1", 2: "Joueur 2"}}
        self.modes = self.reglages['modes']
        self.noms = self.reglages['noms']
        self.humains = [1, 2]                # numéros des joueurs humains
        self.selection = None                # domino (objet Domino) sélectionné par le joueur
        self.mains_affichees = []            # dominos de la main affichée, dans l'ordre d'affichage
        self.jeton = 0                       # change à chaque nouvelle manche : annule les actions de l'IA en retard
        self.ia_reflechit = False
        self.joueur_revele = None            # (plusieurs humains) joueur qui a cliqué pour voir sa main
        self.dernier_humain = 1              # (plusieurs humains) dernier humain dont la main a été affichée
        self.cp_vu = None                    # joueur courant au dernier rafraîchissement de tour
        self.score_enregistre = False
        self.pont = _PontIA()
        self.pont.termine.connect(self._ia_terminee)
        self._construire()

    # ---------------------------------------------------------------- construction de l'écran
    def _construire(self):
        W = QtWidgets
        racine = W.QVBoxLayout(self)
        racine.setContentsMargins(16, 12, 16, 12)
        racine.setSpacing(8)

        haut = W.QHBoxLayout()
        self.lbl_tour = W.QLabel()
        self.lbl_tour.setObjectName("tour")
        self.lbl_talon = W.QLabel()
        self.lbl_talon.setObjectName("talon")
        self.btn_reglages = W.QPushButton("Réglages")
        self.btn_reglages.clicked.connect(self._demander_reglages)
        haut.addWidget(self.lbl_tour, 1)
        haut.addWidget(self.lbl_talon)
        haut.addWidget(self.btn_reglages)
        racine.addLayout(haut)

        self.lbl_score = W.QLabel()
        self.lbl_score.setObjectName("score")
        self.lbl_score.setWordWrap(True)
        racine.addWidget(self.lbl_score)

        # les adversaires (1 à 3), côte à côte : un nom + une rangée de dominos face cachée chacun
        self.blocs_adv, self.lbls_adv, self.mains_adv = [], [], []
        ligne_adv = W.QHBoxLayout()
        for _ in range(NB_JOUEURS_MAX - 1):
            bloc = W.QWidget()
            lb = W.QVBoxLayout(bloc)
            lb.setContentsMargins(0, 0, 0, 0)
            lb.setSpacing(4)
            lbl = W.QLabel()
            main = MainWidget(S=22)
            lb.addWidget(lbl)
            lb.addWidget(main, 1)
            ligne_adv.addWidget(bloc, 1)
            self.blocs_adv.append(bloc)
            self.lbls_adv.append(lbl)
            self.mains_adv.append(main)
        racine.addLayout(ligne_adv)

        self.chaine_w = ChaineWidget()
        defilement = W.QScrollArea()
        defilement.setWidgetResizable(True)
        defilement.setHorizontalScrollBarPolicy(SANS_BARRE)
        defilement.setWidget(self.chaine_w)
        defilement.setMinimumHeight(170)
        racine.addWidget(defilement, 1)

        self.lbl_message = W.QLabel()
        self.lbl_message.setWordWrap(True)
        racine.addWidget(self.lbl_message)

        self.lbl_main = W.QLabel()
        racine.addWidget(self.lbl_main)
        self.main_w = MainWidget(S=44)
        racine.addWidget(self.main_w)

        # boutons d'action (pendant la manche)
        self.actions = W.QWidget()
        la = W.QHBoxLayout(self.actions)
        la.setContentsMargins(0, 0, 0, 0)
        self.btn_piocher = W.QPushButton("Piocher")
        self.btn_piocher.setObjectName("alerte")
        self.btn_passer = W.QPushButton("Passer son tour")
        self.btn_passer.setObjectName("alerte")
        self.lbl_aide = W.QLabel()
        self.lbl_aide.setObjectName("aide")
        self.lbl_aide.setWordWrap(True)
        la.addWidget(self.btn_piocher)
        la.addWidget(self.btn_passer)
        la.addWidget(self.lbl_aide, 1)
        racine.addWidget(self.actions)

        # bandeau de fin de manche
        self.bandeau = W.QFrame()
        self.bandeau.setObjectName("bandeau")
        lb = W.QHBoxLayout(self.bandeau)
        self.lbl_fin = W.QLabel()
        self.lbl_fin.setObjectName("fin")
        self.lbl_fin.setWordWrap(True)
        btn_nouvelle = W.QPushButton("Nouvelle manche")
        btn_nouvelle.setObjectName("principal")
        btn_autres = W.QPushButton("Changer les réglages")
        lb.addWidget(self.lbl_fin, 1)
        lb.addWidget(btn_nouvelle)
        lb.addWidget(btn_autres)
        racine.addWidget(self.bandeau)
        self.bandeau.hide()

        self.main_w.clique.connect(self._clic_main)
        self.main_w.double_clique.connect(self._double_clic_main)
        self.main_w.revelee.connect(self._reveler)
        self.chaine_w.zone_cliquee.connect(self._clic_zone)
        self.btn_piocher.clicked.connect(self._piocher)
        self.btn_passer.clicked.connect(self._passer)
        btn_nouvelle.clicked.connect(self.nouvelle_manche)
        btn_autres.clicked.connect(self._demander_reglages)

    # ---------------------------------------------------------------- démarrage
    def demarrer(self, reglages):
        """Nouvelle partie (score remis à zéro) avec les réglages choisis."""
        self.reglages = reglages
        self.modes = reglages['modes']
        self.noms = reglages['noms']
        self.humains = [j for j in sorted(self.modes) if self.modes[j] == HUMAIN]
        self.score = Score(len(self.modes))
        self.nouvelle_manche()

    def nouvelle_manche(self):
        """Nouvelle manche, le score est conservé."""
        self.jeton += 1                      # annule les timers / threads de la manche précédente
        self.partie = Partie(self.modes, self.reglages.get('profs', {}))
        self.selection = None
        self.joueur_revele = None
        self.dernier_humain = self.humains[0]
        self.cp_vu = None
        self.score_enregistre = False
        self.ia_reflechit = False
        self._apres_action()

    def _demander_reglages(self):
        self.jeton += 1
        self.retour_reglages.emit()

    # ---------------------------------------------------------------- affichage
    def _plusieurs_humains_caches(self):
        """Vrai quand plusieurs humains partagent l'écran et que les mains doivent rester cachées."""
        return len(self.humains) > 1 and self.reglages.get('cacher', False)

    def _est_masquee(self):
        """Plusieurs humains : la main du joueur courant reste cachée tant qu'il n'a pas cliqué dessus."""
        p = self.partie
        return (self._plusieurs_humains_caches() and not p.fini and not p.est_ia(p.cp)
                and self.joueur_revele != p.cp)

    def _joueur_bas(self):
        """Joueur humain dont la main est affichée en bas de l'écran.
        Un seul humain : toujours lui. Plusieurs : celui qui doit jouer (pendant le tour d'une IA,
        on garde le dernier humain affiché, mais sa main est alors cachée)."""
        p = self.partie
        if len(self.humains) == 1:
            return self.humains[0]
        if not p.est_ia(p.cp):
            self.dernier_humain = p.cp
        return self.dernier_humain

    @staticmethod
    def _trier(dominos):
        return sorted(dominos, key=lambda d: tuple(sorted(d.t())))

    def _pioche_visible(self, joueur):
        """Le domino pioché par `joueur` peut-il être affiché dans le journal ? Jamais pour une IA ;
        pour un humain, sauf si d'autres humains regardent l'écran avec les mains cachées."""
        if self.partie.est_ia(joueur):
            return False
        return not self._plusieurs_humains_caches()

    def _texte_evenement(self, ev):
        genre, joueur = ev[0], ev[1]
        nom = self.noms[joueur]
        if genre == 'ouverture':
            return "%s ouvre la manche avec [%d|%d]." % (nom, ev[2][0], ev[2][1])
        if genre == 'pose':
            cote = "à gauche" if ev[3] == 'left' else "à droite"
            return "%s pose [%d|%d] %s." % (nom, ev[2][0], ev[2][1], cote)
        if genre == 'pioche':
            if self._pioche_visible(joueur):
                return "%s pioche [%d|%d]." % (nom, ev[2][0], ev[2][1])
            return "%s pioche un domino." % nom
        return "%s passe son tour (talon vide)." % nom

    def _texte_fin(self):
        p, n = self.partie, self.noms
        reste = "Points restants : %s." % ", ".join("%s %d" % (n[j], p.totaux[j]) for j in sorted(p.totaux))
        if p.gagnant == 0:
            egaux = " et ".join(n[j] for j in p.ex_aequo)
            return "Partie bloquée : égalité entre %s ! %s" % (egaux, reste)
        if p.bloquee:
            return "Partie bloquée. %s gagne la manche (+%d pts). %s" % (n[p.gagnant], p.points, reste)
        return "%s a posé son dernier domino : manche gagnée (+%d pts). %s" % (n[p.gagnant], p.points, reste)

    def rafraichir(self):
        p = self.partie
        if p is None:
            return
        n = self.noms
        bas = self._joueur_bas()             # joueur dont la main est affichée en bas
        # adversaires, dans l'ordre du tour à partir du joueur du bas
        adversaires = [(bas - 1 + k) % p.np + 1 for k in range(1, p.np)]
        humain_agit = (not p.fini) and (not p.est_ia(p.cp))
        masquee = self._est_masquee()

        # en-tête : tour, talon, score
        if p.fini:
            tour = "Manche terminée"
        elif p.est_ia(p.cp):
            tour = "%s %s" % (n[p.cp], "réfléchit…" if self.ia_reflechit else "joue…")
        else:
            tour = "À %s de jouer" % n[p.cp]
        self.lbl_tour.setText(tour)
        self.btn_reglages.setEnabled(not self.ia_reflechit)   # pas de changement de réglages pendant que l'IA calcule
        self.lbl_talon.setText("Talon : %d" % len(p.talon))
        s = self.score
        texte_score = "Score — " + "   |   ".join(
            "%s : %d pts (%d manche(s))" % (n[j], s.points[j], s.manches[j]) for j in sorted(self.modes))
        if s.nuls:
            texte_score += "   |   égalités : %d" % s.nuls
        self.lbl_score.setText(texte_score)

        # chaîne
        cotes = set()
        if self.selection is not None and humain_agit:
            cotes = set(p.cotes_legaux(self.selection))
        tuiles = [d.t() for d in p.chaine.dom_list()]
        dernier = None
        if p.dernier_cote is not None:
            dernier = 0 if p.dernier_cote == 'left' else len(tuiles) - 1
        self.chaine_w.set_etat(tuiles, p.chaine.ex(), cotes, dernier)

        # adversaires (dominos face cachée jusqu'à la fin de la manche) ; le joueur courant est marqué ▶
        for i, bloc in enumerate(self.blocs_adv):
            if i >= len(adversaires):
                bloc.setVisible(False)
                continue
            j = adversaires[i]
            main_j = self._trier(p.jeu[j])
            marque = "▶ " if (j == p.cp and not p.fini) else ""
            self.lbls_adv[i].setText("%s%s : %d domino(s) en main" % (marque, n[j], len(main_j)))
            self.mains_adv[i].set_etat([tuple(sorted(d.t())) for d in main_j], dos=not p.fini)
            bloc.setVisible(True)

        # main du joueur affiché en bas
        mains = self._trier(p.jeu[bas])
        self.mains_affichees = mains
        jouables = None
        if humain_agit and bas == p.cp and not masquee:
            jouables = {i for i, d in enumerate(mains) if p.cotes_legaux(d)}
        indice_selection = None
        if self.selection is not None and self.selection in mains:
            indice_selection = mains.index(self.selection)
        marque = "▶ " if (bas == p.cp and not p.fini) else ""
        self.lbl_main.setText("%sMain de %s" % (marque, n[bas]))
        # pendant le tour d'une IA, avec plusieurs humains : la main affichée reste face cachée
        face_cachee = self._plusieurs_humains_caches() and not p.fini and p.est_ia(p.cp)
        self.main_w.set_etat([tuple(sorted(d.t())) for d in mains], jouables=jouables,
                             selection=indice_selection, dos=face_cachee, masquee=masquee,
                             texte_masque="%s : cliquez ici pour afficher votre main" % n[bas])

        # message, boutons et aide
        self.lbl_message.setText("   •   ".join(self._texte_evenement(e) for e in p.evenements[-p.np:]))
        etat = p.etat_tour()
        peut_agir = humain_agit and not masquee
        self.btn_piocher.setEnabled(peut_agir and etat == 'piocher')
        self.btn_passer.setEnabled(peut_agir and etat == 'passer')
        if not peut_agir:
            aide = ""
        elif etat == 'piocher':
            aide = "Aucun coup possible : piochez un domino."
        elif etat == 'passer':
            aide = "Aucun coup possible et le talon est vide : passez votre tour."
        elif self.selection is not None:
            aide = "Cliquez sur une zone verte (◀ ou ▶) pour poser le domino."
        else:
            aide = "Cliquez sur un domino à cadre vert, puis sur l'extrémité voulue (double-clic : pose directe)."
        self.lbl_aide.setText(aide)

        self.actions.setVisible(not p.fini)
        self.bandeau.setVisible(p.fini)
        if p.fini:
            self.lbl_fin.setText(self._texte_fin())

    # ---------------------------------------------------------------- actions du joueur humain
    def _humain_peut_agir(self):
        p = self.partie
        return p is not None and not p.fini and not p.est_ia(p.cp) and not self._est_masquee()

    def _reveler(self):
        self.joueur_revele = self.partie.cp
        self.rafraichir()

    def _clic_main(self, i):
        if not self._humain_peut_agir() or i >= len(self.mains_affichees):
            return
        domino = self.mains_affichees[i]
        if not self.partie.cotes_legaux(domino):
            self.lbl_message.setText("Ce domino ne peut pas être posé sur la chaîne.")
            return
        self.selection = None if self.selection is domino else domino
        self.rafraichir()

    def _double_clic_main(self, i):
        if not self._humain_peut_agir() or i >= len(self.mains_affichees):
            return
        domino = self.mains_affichees[i]
        cotes = self.partie.cotes_legaux(domino)
        if len(cotes) == 1:                  # un seul côté possible : on pose tout de suite
            self.partie.poser(domino, cotes[0])
            self._apres_action()

    def _clic_zone(self, cote):
        if not self._humain_peut_agir() or self.selection is None:
            return
        if cote in self.partie.cotes_legaux(self.selection):
            self.partie.poser(self.selection, cote)
            self._apres_action()

    def _piocher(self):
        if not self._humain_peut_agir():
            return
        try:
            self.partie.piocher()
        except ValueError:
            return
        self._apres_action()

    def _passer(self):
        if not self._humain_peut_agir():
            return
        try:
            self.partie.passer()
        except ValueError:
            return
        self._apres_action()

    # ---------------------------------------------------------------- enchaînement des tours
    def _apres_action(self):
        """Appelée après chaque action : met à jour l'écran, enregistre le score en fin de manche,
        et fait jouer l'IA si c'est à elle (plusieurs IA de suite : elles s'enchaînent toutes seules)."""
        p = self.partie
        self.selection = None
        self.ia_reflechit = False
        if p.cp != self.cp_vu:               # le tour a changé de main : la main redevient cachée
            self.joueur_revele = None
            self.cp_vu = p.cp
        if p.fini and not self.score_enregistre:
            self.score.enregistrer(p)
            self.score_enregistre = True
        if p.fini or not p.est_ia(p.cp):
            self.rafraichir()
            return
        etat = p.etat_tour()
        self.ia_reflechit = (etat == 'jouer')
        self.rafraichir()
        jeton = self.jeton
        if etat == 'jouer':
            QtCore.QTimer.singleShot(500, lambda: self._lancer_ia(jeton))
        else:
            QtCore.QTimer.singleShot(800, lambda: self._ia_pioche_ou_passe(jeton))

    def _ia_pioche_ou_passe(self, jeton):
        if jeton != self.jeton or self.partie.fini:
            return
        etat = self.partie.etat_tour()
        if etat == 'piocher':
            self.partie.piocher()
        elif etat == 'passer':
            self.partie.passer()
        self._apres_action()

    def _lancer_ia(self, jeton):
        """Calcule le coup de l'IA dans un thread, pour que la fenêtre ne se fige pas."""
        if jeton != self.jeton or self.partie.fini:
            return
        partie = self.partie

        def travail():
            try:
                coup = partie.choisir_coup_ia()
            except Exception as erreur:
                print("erreur de l'IA :", repr(erreur))
                coup = None
            try:
                self.pont.termine.emit(jeton, coup)
            except RuntimeError:             # fenêtre déjà fermée
                pass

        threading.Thread(target=travail, daemon=True).start()

    def _ia_terminee(self, jeton, coup):
        p = self.partie
        if jeton != self.jeton or p.fini or not p.est_ia(p.cp):
            return                           # résultat d'une manche abandonnée
        if coup is None:                     # l'IA a planté : coup légal au hasard
            domino = random.choice(p.jouables())
            cote = random.choice(p.cotes_legaux(domino))
        else:
            domino, cote = coup
        p.poser(domino, cote)
        self._apres_action()


# ----------------------------------------------------------------------------- fenêtre principale
class Fenetre(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Domino")
        self.resize(1000, 780)
        self.pile = QtWidgets.QStackedWidget()
        self.page_reglages = PageReglages()
        self.page_jeu = PageJeu()
        self.pile.addWidget(self.page_reglages)
        self.pile.addWidget(self.page_jeu)
        self.setCentralWidget(self.pile)
        self.page_reglages.demarrer.connect(self._demarrer)
        self.page_jeu.retour_reglages.connect(self._retour_reglages)

    def _demarrer(self, reglages):
        self.page_jeu.demarrer(reglages)
        self.pile.setCurrentWidget(self.page_jeu)

    def _retour_reglages(self):
        self.pile.setCurrentWidget(self.page_reglages)

    def closeEvent(self, evenement):
        self.page_jeu.jeton += 1             # on neutralise les actions de l'IA en attente
        super().closeEvent(evenement)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(palette_claire())
    app.setStyleSheet(STYLE)
    fenetre = Fenetre()
    fenetre.show()
    sys.exit(app.exec() if hasattr(app, "exec") else app.exec_())


if __name__ == "__main__":
    main()
