import random
import unittest

from dominos_main import (
    Domino,
    Chain,
    ensemble,
    distribute,
    guess_repartition_1p,
    guess_repartition,
    complementary,
    anonymous_dominos,
    can_play,
    playable_dominos,
    remove,
    choose_alea,
    choose_naive,
    minmax,
    choose_minmax,
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
        # Chain prend ici une liste de dominos, d'apres dominos_main.py
        self.chaine = Chain([Domino((2, 3))])

    def test_init_extremites(self):
        self.assertEqual(self.chaine.ex(), (2, 3))

    def test_plateau_initial(self):
        self.assertEqual(self.chaine.plateau(), [(2, 3)])

    def test_dom_list(self):
        doms = [Domino((1, 2))]
        chaine = Chain(doms)
        self.assertEqual([d.t() for d in chaine.dom_list()], [(1, 2)])

    def test_push(self):
        self.chaine.push(Domino((3, 6)), 'right')
        self.assertEqual(self.chaine.plateau(), [(2, 3), (3, 6)])
        self.assertEqual(self.chaine.ex(), (2, 6))
        self.chaine.push(Domino((5, 2)), 'left')
        self.assertEqual(self.chaine.plateau(), [(5, 2), (2, 3), (3, 6)])
        self.assertEqual(self.chaine.ex(), (5, 6))
        self.chaine.push(Domino((6, 4)), 'right')
        self.chaine.push(Domino((1, 5)), 'left')
        self.assertEqual(self.chaine.plateau(), [(1, 5), (5, 2), (2, 3), (3, 6), (6, 4)])
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

    def test_lengths_2p(self):
        # 28 dominos, 3 tas (2 joueurs + talon) : 9 dominos par joueur, 10 au talon
        random.seed(42)
        jeu_p, talon, cp, biggest = distribute(self.jeu, 2)
        self.assertEqual(set(jeu_p.keys()), {1, 2})
        self.assertEqual(len(jeu_p[1]), 9)
        self.assertEqual(len(jeu_p[2]), 9)
        self.assertEqual(len(talon), 10)

    def test_lengths_3p(self):
        # 28 dominos, 4 tas (3 joueurs + talon) : 7 dominos par joueur, 7 au talon
        random.seed(42)
        jeu_p, talon, cp, biggest = distribute(self.jeu, 3)
        self.assertEqual(set(jeu_p.keys()), {1, 2, 3})
        self.assertEqual(len(jeu_p[1]), 7)
        self.assertEqual(len(jeu_p[2]), 7)
        self.assertEqual(len(jeu_p[3]), 7)
        self.assertEqual(len(talon), 7)

    def test_distinct(self):
        random.seed(42)
        jeu_p, talon, _, _ = distribute(self.jeu, 2)
        toutes = [d.t() for main in jeu_p.values() for d in main] + [d.t() for d in talon]
        self.assertEqual(len(toutes), 28)
        self.assertEqual(len(set(toutes)), 28)

    def test_beginning_player(self):
        random.seed(42)
        jeu_p, talon, cp, biggest = distribute(self.jeu, 2)
        self.assertIn(cp, jeu_p.keys())
        # si une main contient un double, le domino de depart doit etre le plus grand double
        doubles = [d for main in jeu_p.values() for d in main if d.db()]
        if doubles:
            self.assertTrue(biggest.db())
            self.assertEqual(biggest.val(), max(d.val() for d in doubles))


class TestComplementary(unittest.TestCase):

    def test_complementary(self):
        l = [Domino((0, 1)), Domino((1, 2)), Domino((2, 3)), Domino((3, 4))]
        sl = [Domino((0, 1)), Domino((2, 3))]
        comp = complementary(l, sl)
        self.assertEqual(sorted(d.t() for d in comp), [(1, 2), (3, 4)])

    def test_nothing_if_all_taken(self):
        l = [Domino((0, 1)), Domino((1, 2))]
        sl = [Domino((0, 1)), Domino((1, 2))]
        self.assertEqual(complementary(l, sl), [])

    def test_all_if_empty(self):
        l = [Domino((0, 1)), Domino((1, 2))]
        self.assertEqual([d.t() for d in complementary(l, [])], [(0, 1), (1, 2)])


class TestGuessRepartition1p(unittest.TestCase):

    def setUp(self):
        self.l = [Domino((0, 1)), Domino((1, 2)), Domino((2, 3)), Domino((3, 4))]

    def test_invariants(self):
        guesses = guess_repartition_1p(self.l, 2)
        self.assertTrue(len(guesses) > 0)
        for guess, talon in guesses:
            # chaque main supposee a exactement la taille demandee
            self.assertEqual(len(guess), 2)
            # main + talon = tous les dominos, sans doublon ni oubli
            toutes = [d.t() for d in guess] + [d.t() for d in talon]
            self.assertEqual(len(toutes), len(self.l))
            self.assertEqual(len(set(toutes)), len(self.l))
            self.assertEqual(sorted(toutes), sorted(d.t() for d in self.l))

    def test_full_hand(self):
        # si la main fait la taille de la liste, il n'y a qu'une seule distribution
        guesses = guess_repartition_1p(self.l, 4)
        self.assertEqual(len(guesses), 1)
        guess, talon = guesses[0]
        self.assertEqual([d.t() for d in guess], [d.t() for d in self.l])
        self.assertEqual(talon, [])


class TestGuessRepartition(unittest.TestCase):

    def test_two_players(self):
        l = [Domino((0, 1)), Domino((1, 2)), Domino((2, 3)), Domino((3, 4)), Domino((4, 5))]
        reps = guess_repartition(l, [2, 2], 1)
        self.assertTrue(len(reps) > 0)
        for rep in reps:
            # une repartition complete pour 2 joueurs : un couple de mains
            self.assertEqual(len(rep), 2)
            self.assertEqual(len(rep[0]), 2)
            self.assertEqual(len(rep[1]), 2)
            toutes = [d.t() for main in rep for d in main]
            # les deux mains contiennent 4 dominos distincts pris dans la liste
            self.assertEqual(len(set(toutes)), 4)
            self.assertEqual(len(toutes), 4)


class TestAnonymousDominos(unittest.TestCase):

    def test_anonymous(self):
        main = [Domino((0, 1)), Domino((1, 2))]
        plateau = Chain([Domino((2, 3)), Domino((3, 6)), Domino((5, 2))])
        lad = anonymous_dominos(main, plateau)
        valeurs = [d.t() for d in lad]
        # 28 dominos moins les 5 deja visibles
        self.assertEqual(len(lad), 23)
        self.assertNotIn((0, 1), valeurs)
        self.assertNotIn((3, 6), valeurs)
        self.assertIn((4, 4), valeurs)
        self.assertIn((6, 6), valeurs)


class TestCanPlay(unittest.TestCase):

    def test_can_play(self):
        plateau = Chain([Domino((2, 3))])
        main = [Domino((2, 5))]
        self.assertTrue(can_play(main, plateau))
        plateau = Chain([Domino((2, 3))])
        main = [Domino((6, 3))]
        self.assertTrue(can_play(main, plateau))
        plateau = Chain([Domino((2, 3))])
        main = [Domino((5, 6)), Domino((0, 4))]
        self.assertFalse(can_play(main, plateau))
        plateau = Chain([Domino((2, 3))])
        self.assertFalse(can_play([], plateau))
        plateau = Chain([Domino((0, 0))])
        self.assertFalse(can_play([Domino((1, 2))], plateau))


class TestPlayableDominos(unittest.TestCase):

    def test_playable_dominos(self):
        plateau = Chain([Domino((2, 3))])
        main = [Domino((2, 5)), Domino((5, 6)), Domino((3, 3)), Domino((1, 4))]
        jouables = playable_dominos(main, plateau)
        valeurs = {d.t() for d in jouables}
        self.assertEqual(valeurs, {(2, 5), (3, 3)})

    def test_no_playable(self):
        plateau = Chain([Domino((5, 6))])
        main = [Domino((1, 2)), Domino((3, 4))]
        self.assertEqual(playable_dominos(main, plateau), [])

    def test_all_playable(self):
        plateau = Chain([Domino((3, 3))])
        main = [Domino((3, 0)), Domino((2, 3))]
        self.assertEqual(len(playable_dominos(main, plateau)), 2)


class TestRemove(unittest.TestCase):

    def test_remove(self):
        pile = [Domino((1, 2)), Domino((3, 4)), Domino((5, 6))]
        cible = pile[1]
        remove(cible, pile)
        self.assertEqual(len(pile), 2)
        self.assertNotIn(cible.t(), [d.t() for d in pile])

    def test_nothing_if_not_in(self):
        pile = [Domino((1, 2)), Domino((3, 4))]
        remove(Domino((6, 6)), pile)
        self.assertEqual(len(pile), 2)

    def test_keep_all_others(self):
        pile = [Domino((0, 1)), Domino((2, 2)), Domino((4, 5))]
        d = pile[1]
        remove(d, pile)
        self.assertEqual([d.t() for d in pile], [(0, 1), (4, 5)])

    def test_remove_last(self):
        pile = [Domino((1, 2)), Domino((3, 4))]
        d = pile[1]
        remove(d, pile)
        self.assertEqual([x.t() for x in pile], [(1, 2)])

    def test_remove_only_element(self):
        pile = [Domino((1, 1))]
        d = pile[0]
        remove(d, pile)
        self.assertEqual(pile, [])


class TestChooseAlea(unittest.TestCase):

    def test_choose_alea_in_range(self):
        random.seed(42)
        mains = [Domino((1, 2)), Domino((3, 4)), Domino((5, 6))]
        for _ in range(50):
            i = choose_alea(mains)
            self.assertTrue(0 <= i < 3)


class TestChooseNaive(unittest.TestCase):

    def test_choose_naive(self):
        mains = [Domino((1, 2)), Domino((2, 2)), Domino((0, 3))]
        self.assertEqual(choose_naive(mains), 1)

    def test_choose_naive_tie_keeps_first(self):
        mains = [Domino((3, 4)), Domino((6, 1))]
        self.assertEqual(choose_naive(mains), 0)


class TestMinmax(unittest.TestCase):

    def test_last_domino_ia(self):
        # l'ia n'a plus qu'un domino jouable : elle doit le jouer (score -inf)
        jeu = {1: [Domino((3, 6))], 2: [Domino((0, 1))]}
        plateau = Chain([Domino((2, 3))])
        result = minmax(jeu, plateau, 1, 0, 1, 2, 1, 0, [])
        self.assertEqual(result, (float('-inf'), 0, 'right'))

    def test_last_domino_adversaire(self):
        # l'adversaire n'a plus qu'un domino jouable : score +inf pour l'ia
        jeu = {1: [Domino((0, 1))], 2: [Domino((3, 6))]}
        plateau = Chain([Domino((2, 3))])
        result = minmax(jeu, plateau, 1, 0, 1, 2, 1, 0, [])
        self.assertEqual(result, (float('inf'), 0, 'right'))

    def test_max_prof_reached(self):
        # profondeur max atteinte : l'evaluation est la somme des points de l'ia
        jeu = {1: [Domino((6, 6)), Domino((5, 5))], 2: [Domino((0, 1))]}
        plateau = Chain([Domino((2, 3))])
        result = minmax(jeu, plateau, 0, 0, 1, 2, 1, 0, [])
        self.assertEqual(result, (22, 0, 'right'))


class TestChooseMinmax(unittest.TestCase):

    def test_ia_last_domino(self):
        # l'ia (joueur 2) n'a qu'un domino, jouable : elle doit le jouer a droite
        jeu = {1: [Domino((0, 1))], 2: [Domino((3, 3))]}
        plateau = Chain([Domino((2, 3))])
        result = choose_minmax(jeu, plateau, 2, 2, 1, 0)
        self.assertEqual(result, (0, 'right'))


if __name__ == "__main__":
    unittest.main()