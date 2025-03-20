#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

class PrefixTreeNode:
    """
    Repr�sente un n�ud dans un arbre pr�fix� monophonique lin�aire.
    Chaque n�ud ne poss�de qu'un seul enfant (car l'arbre est lin�aire)
    et une unique continuation (la note associ�e � toute la branche).
    """
    def __init__(self):
        self.child = None
        self.continuation = None

class PrefixTreeContinuator:
    """
    Continuateur monophonique bas� sur la m�thode de Fran�ois Pachet.
    
    Pour une s�quence [A, B, C, D], il cr�e exactement 3 arbres distincts :
      - k = 1 : Pr�fixe [A] ? branche = [A] avec continuation = B.
      - k = 2 : Pr�fixe [A, B] ? branche = [B, A] avec continuation = C.
      - k = 3 : Pr�fixe [A, B, C] ? branche = [C, B, A] avec continuation = D.
    """
    def __init__(self, silence_threshold=2.0):
        self.roots = {}   # Dictionnaire : cl� = racine (premier �l�ment du pr�fixe invers�), valeur = l'arbre
        self.sequences = []  # Liste des s�quences (listes de notes)
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Entra�ne l'arbre avec une s�quence donn�e.
        On consid�re uniquement la hauteur des notes.
        Pour chaque k de 1 � len(sequence)-1, on construit un arbre lin�aire
        en inversant le pr�fixe [s?,..., s???] et on associe la continuation s?.
        """
        notes = [note for note, dur in sequence]
        self.sequences.append(notes)

        # Pour k variant de 1 � len(notes)-1
        for k in range(1, len(notes)):
            prefix = notes[:k]         # Sous-s�quence [s?, ..., s???]
            cont = notes[k]            # La continuation est la note s?
            rev_prefix = prefix[::-1]  # Inversion du pr�fixe : [s???, ..., s?]
            root_note = rev_prefix[0]  # La racine de cet arbre est s???

            # Si cet arbre n'existe pas encore, le cr�er
            if root_note not in self.roots:
                self.roots[root_note] = PrefixTreeNode()
            node = self.roots[root_note]

            # Parcourir rev_prefix (� partir du 2�me �l�ment)
            for note in rev_prefix[1:]:
                if node.child is None:
                    node.child = PrefixTreeNode()
                node = node.child

            # D�finir la continuation unique pour toute cette branche
            if node.continuation is None:
                node.continuation = cont

    def display_memory(self):
        """Affiche l'ensemble des arbres pr�fix�s construits."""
        print("\n?? **Arbres pr�fix�s - M�moire des s�quences enregistr�es**")
        # Pour chaque arbre, on affiche la branche compl�te avec la continuation
        for root_note, root in self.roots.items():
            print(f"\n?? Racine : {root_note}")
            self.display_tree(root, [root_note], level=1)

    def display_tree(self, node, branch, level):
        indent = "    " * level
        # Affichage de la branche actuelle avec la continuation
        if node.continuation is not None:
            print(f"{indent}{' -> '.join(map(str, branch))} [ {node.continuation} ]")
        else:
            print(f"{indent}{' -> '.join(map(str, branch))}")
        if node.child is not None:
            self.display_tree(node.child, branch + [node.child.continuation if node.child.continuation is not None else "?"], level+1)

    def generate(self, seed, length=10):
        """
        G�n�re une continuation en se basant sur la s�quence d'entr�e (seed).
        Pour la g�n�ration, on utilise le seed complet comme base, et on choisit l'arbre
        correspondant � la sous-s�quence la plus longue.
        Ici, pour simplifier, nous ne fusionnons pas les arbres existants ; 
        on se contente de parcourir l'arbre dont la racine correspond � la derni�re note du seed.
        """
        if not self.sequences:
            print("?? Aucun apprentissage disponible, g�n�ration impossible.")
            return []

        # Utiliser le seed complet (liste de tuples) pour extraire les notes
        generated = [note for note, dur in seed]
        # Pour la g�n�ration, on choisit l'arbre dont la racine est la derni�re note du seed invers�.
        # Or, selon notre construction, le seed doit �tre la s�quence enti�re.
        # Par simplicit�, nous utilisons la derni�re note du seed comme crit�re.
        root_note = generated[-1]
        if root_note not in self.roots:
            print("?? Aucun arbre correspondant trouv�, g�n�ration impossible.")
            return []
        node = self.roots[root_note]
        branch = [root_note]
        for _ in range(length):
            if node.child is not None and node.child.continuation is not None:
                next_note = node.child.continuation
                branch.append(next_note)
                node = node.child
            else:
                print("?? Fin de la branche, g�n�ration termin�e.")
                break
        generated.extend(branch[1:])  # Ajouter la branche (hors la premi�re note d�j� pr�sente)
        print("\n?? **Continuation g�n�r�e**:")
        print("??", " -> ".join(map(str, generated)))
        return generated

    def play_output(self, notes):
        """Simule la lecture MIDI en affichant la s�quence g�n�r�e."""
        print("\n[PLAY OUTPUT]")
        print("Notes jou�es :", " -> ".join(map(str, notes)))

# ------------------- Mode Test -------------------
if __name__ == '__main__':
    continuator = PrefixTreeContinuator(silence_threshold=2.0)

    # S�quence 1 : [48, 50, 52, 53] (Do, R�, Mi, Fa)
    sequence1 = [(48, 0.5), (50, 0.5), (52, 0.5), (53, 0.5)]
    print("=== Entra�nement avec la s�quence 1 : Do, R�, Mi, Fa (48, 50, 52, 53) ===")
    continuator.train(sequence1)
    continuator.display_memory()

    print("\n=== G�n�ration pour la s�quence 1 ===")
    continuation1 = continuator.generate(sequence1, length=10)
    print("Continuation g�n�r�e :", continuation1)

    # Simuler un silence (ici, on n'attend pas vraiment, on passe � la s�quence 2)
    time.sleep(2)

    # S�quence 2 : [48, 50, 50, 52] (Do, R�, R�, Mi)
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entra�nement avec la s�quence 2 : Do, R�, R�, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)
    continuator.display_memory()

    print("\n=== G�n�ration pour la s�quence 2 ===")
    continuation2 = continuator.generate(sequence2, length=10)
    print("Continuation g�n�r�e :", continuation2)
