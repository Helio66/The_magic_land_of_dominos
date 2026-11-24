list[Domino] = [Domino((i,j)) for i in range(7) for j in range(i,7)]

jeu_simule = [l[k]]

def jeux_possible(ensemble, jeu_ia, plateau, talon, jeu_humain) :
    n_talon = len(talon)
    n_joueur = len(jeu_humain)
    l = []
    jeux_poss = []
    talons_poss = []
    for d in ensemble :
        if d not in jeu_ia and d not in plateau :
            l.append(d)
    indices = [i for i in range(len(l))]
    for j in range(n_joueur) :
        k = random.randint(0, len(indices)-1)
        ind = indices[k]









    for k in range(len(l)//n_joueur) :
        for i in range(k*n_joueur, (k+1)*n_joueur) :
            jeu_simule = l[i+ k*n_joueur]
            jeux_poss[k] = jeu_simule

                if d not in jeu_simule :
                    talon_simule = [d for i in range(n_talon)]
                    talons_poss.append(talon_simule)
    return jeux_poss, talons_poss

'''for i in range(len(jeu) // (np + 1)):  # on repartit les cartes. le reste est mis dans le talon
    for j in range(np):
        if j + 1 in jeu_p:
            jeu_p[j + 1].append(jeu[j * taille_jeu + i])'''