"""
Tests unitaires pour dominos_main.py
Lancement :  python -m unittest test_dominos.py -v

IMPORTANT : dans dominos_main.py, il faut remplacer le dernier appel
    play()
par
    if __name__ == "__main__":
        play()
Sinon l'import du module lance une partie interactive et les tests bloquent.
"""

import random
import unittest

from dominos_main import (
    Domino,
    Chain,
    distribute,
    can_play,
    playable_dominos,
    remove,
    ensemble,
)


class TestDomino(unittest.TestCase):

    def test_t(self):
        d = Domino((3, 5))
        self.assertEqual(d.t(), (3, 5))

    def test_val(self):
        self.assertEqual(Domino((2, 4)).val(), 6)
        self.assertEqual(Domino((0, 0)).val(), 0)
        self.assertEqual(Domino((6, 6)).val(), 12)

    def test_double(self):
        for i in range(7):
            self.assertTrue(Domino((i, i)).db())
        self.assertFalse(Domino((1, 2)).db())
        self.assertFalse(Domino((0, 6)).db())

    def test_inv(self):
        d = Domino((1, 4))
        d.inv()
        self.assertEqual(d.t(), (4, 1))
        d = Domino((2, 5))
        d.inv()
        d.inv()
        self.assertEqual(d.t(), (2, 5))
        d = Domino((3, 3))
        d.inv()
        self.assertEqual(d.t(), (3, 3))

    def test_val_inv(self):
        d = Domino((2, 6))
        avant = d.val()
        d.inv()
        self.assertEqual(d.val(), avant)


class TestChain(unittest.TestCase):

    def setUp(self):
        self.chaine = Chain(Domino((2, 3)))

    def test_init_extremites(self):
        self.assertEqual(self.chaine.ex(), (2, 3))

    def test_plateau_initial(self):
        self.assertEqual(self.chaine.plateau(), [(2, 3)])

    def test_push(self):
        self.chaine.push(Domino((3, 6)), 'right')
        self.assertEqual(self.chaine.plateau(), [(2, 3), (3, 6)])
        self.assertEqual(self.chaine.ex(), (2, 6))
        self.chaine.push(Domino((5, 2)), 'left')
        self.assertEqual(self.chaine.plateau(), [(5, 2), (2, 3), (3,6)])
        self.assertEqual(self.chaine.ex(), (5, 3))
        self.chaine.push(Domino((3, 4)), 'right')
        self.chaine.push(Domino((1, 2)), 'left')
        self.assertEqual(self.chaine.plateau(), [(1, 2), (2, 3), (3, 4)])
        self.assertEqual(self.chaine.ex(), (1, 4))

class TestEnsemble(unittest.TestCase):

    def test_ensemble(self):
        self.assertEqual(len(ensemble), 28)
        valeurs = [d.t() for d in ensemble]
        self.assertEqual(len(set(valeurs)), 28)

class TestDistribute(unittest.TestCase):

    def setUp(self):
        # copie pour ne pas melanger l'ensemble global plusieurs fois
        self.jeu = [Domino((i, j)) for i in range(7) for j in range(i, 7)]

    def test_length(self):
        random.seed(42)
        p1, p2, talon, cp, biggest = distribute(self.jeu)
        self.assertEqual(len(p1), 7)
        self.assertEqual(len(p2), 7)
        self.assertEqual(len(talon), 14)

    def test_distinct(self):
        random.seed(42)
        p1, p2, talon, _, _ = distribute(self.jeu)
        toutes = [d.t() for d in p1 + p2 + talon]
        self.assertEqual(len(toutes), 28)
        self.assertEqual(len(set(toutes)), 28)

    def test_biggest_domino(self):
        # 14 dominos par joueur : les mains contiennent forcement un double
        for seed in range(10):
            random.seed(seed)
            p1, p2, _, _, biggest = distribute(self.jeu)
            self.assertTrue(biggest.db(),f"seed={seed} : le plus grand domino devrait etre un double")
        for seed in range(10):
            random.seed(seed)
            p1, p2, _, _, biggest = distribute(self.jeu)
            doubles = [d for d in p1 + p2 if d.db()]
            self.assertEqual(biggest.val(), max(d.val() for d in doubles))

class TestCanPlay(unittest.TestCase):

    def test_can_play(self):
        plateau = Chain(Domino((2, 3)))
        main = [Domino((2, 5))]
        self.assertTrue(can_play(main, plateau))
        plateau = Chain(Domino((2, 3)))
        main = [Domino((6, 3))]
        self.assertTrue(can_play(main, plateau))
        plateau = Chain(Domino((2, 3)))
        main = [Domino((5, 6)), Domino((0, 4))]
        self.assertFalse(can_play(main, plateau))
        plateau = Chain(Domino((2, 3)))
        self.assertFalse(can_play([], plateau))
        plateau = Chain(Domino((0, 0)))
        self.assertFalse(can_play([Domino((1, 2))], plateau))


class TestPlayableDominos(unittest.TestCase):

    def test_playable_dominos(self):
        plateau = Chain(Domino((2, 3)))
        main = [Domino((2, 5)), Domino((5, 6)), Domino((3, 3)), Domino((1, 4))]
        jouables = playable_dominos(main, plateau)
        valeurs = {d.t() for d in jouables}
        self.assertEqual(valeurs, {(2, 5), (3, 3)})

    def test_no_playable(self):
        plateau = Chain(Domino((5, 6)))
        main = [Domino((1, 2)), Domino((3, 4))]
        self.assertEqual(playable_dominos(main, plateau), [])

    def test_all_playable(self):
        plateau = Chain(Domino((3, 3)))
        main = [Domino((3, 0)), Domino((2, 3))]
        self.assertEqual(len(playable_dominos(main, plateau)), 2)


class TestRemove(unittest.TestCase):

    def test_remove(self):
        pile = [Domino((1, 2)), Domino((3, 4)), Domino((5, 6))]
        cible = Domino((3, 4))
        remove(cible, pile)
        self.assertEqual(len(pile), 2)
        self.assertNotIn(cible.t(), [d.t() for d in pile])

    def test_nothing_if_not_in(self):
        pile = [Domino((1, 2)), Domino((3, 4))]
        remove(Domino((6, 6)), pile)
        self.assertEqual(len(pile), 2)

    def test_keep_all_others(self):
        pile = [Domino((0, 1)), Domino((2, 2)), Domino((4, 5))]
        remove(Domino((2, 2)), pile)
        self.assertEqual({d.t() for d in pile}, {(0, 1), (4, 5)})


if __name__ == "__main__":
    unittest.main()