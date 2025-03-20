#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

class PrefixTreeNode:
    """Repr�sente un n�ud dans un arbre pr�fix� monophonique lin�aire."""
    def __init__(self):
        self.child = None         # Un seul fils (structure lin�aire)
        self.continuation = None   # La continuation unique associ�e � cette branche

class PrefixTreeContinuator:
    """
    Continuateur monophonique bas� sur la m�thode de Fran�ois Pachet.
    
    Pour une s�quence [A, B, C, D] (ex. [48, 50, 52, 53]), il cr�e :
      - Arbre 1 : [48] avec continuation 50.
      - Arbre 2 : [48, 50] (affich� en sens invers� : 50 -> 48) avec continuation 52.
      - Arbre 3 : [48, 50, 52] (affich� en sens invers� : 52 -> 50 -> 48) avec continuation 53.
    """
    def __init__(self, silence_threshold=2.0):
        self.roots = {}         # Dictionnaire : cl� = racine, valeur = arbre lin�aire (PrefixTreeNode)
        self.sequences = []     # Liste des s�quences enregistr�es (listes de notes)
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Entra�ne l'arbre avec une s�quence (liste de tuples (note, dur�e)). 
        Seules les hauteurs sont utilis�es.
        Pour chaque k de 1 � len(sequence)-1, on extrait le pr�fixe = sequence[0:k]
        et la continuation = sequence[k].
        Le pr�fixe est renvers� pour obtenir une branche lin�aire dont la racine est le premier �l�ment
        du pr�fixe invers�.
        """
        # Extraction des hauteurs
        notes = [note for note, dur in sequence]
        self.sequences.append(notes)

        # Pour chaque pr�fixe commen�ant au d�but et se terminant � l'index k-1, avec continuation notes[k]
        for k in range(1, len(notes)):
            prefix = notes[:k]           # Pr�fixe de longueur k (du d�but)
            cont = notes[k]              # La note qui suit ce pr�fixe
            rev_prefix = prefix[::-1]    # Inversion du pr�fixe pour obtenir la branche lin�aire

            # La racine de l'arbre pour ce pr�fixe est le premier �l�ment de rev_prefix
            root_note = rev_prefix[0]
            if root_note not in self.roots:
                self.roots[root_note] = PrefixTreeNode()
            node = self.roots[root_note]

            # Parcourir rev_prefix (� partir du deuxi�me �l�ment)
            for note in rev_prefix[1:]:
                if node.child is None:
                    node.child = PrefixTreeNode()
                node = node.child
                # On ne modifie pas la continuation si elle existe d�j�

            # D�finir la continuation unique pour cette branche, si elle n'est pas d�j� d�finie
            if node.continuation is None:
                node.continuation = cont

    def display_memory(self):
        """Affiche la m�moire sous forme d'arbres pr�fix�s lin�aires distincts."""
        print("\n?? **Arbres pr�fix�s - M�moire des s�quences enregistr�es**")
        for root_note, root in self.roots.items():
            print(f"\n?? Racine : {root_note}")
            self.display_tree(root, [root_note], level=1)

    def display_tree(self, node, branch, level):
        indent = "    " * level
        if node.continuation is not None:
            print(f"{indent}{' -> '.join(map(str, branch))} [ {node.continuation} ]")
        else:
            print(f"{indent}{' -> '.join(map(str, branch))}")
        if node.child is not None:
            # Puisque l'arbre est lin�aire, il n'y a qu'un seul enfant
            self.display_tree(node.child, branch + [node.child.continuation if node.child.continuation is not None else ""], level+1)

    def generate(self, seed, length=10):
        """
        G�n�re une continuation monophonique.
        Pour le seed, on utilise la s�quence enregistr�e. On choisit l'arbre correspondant
        � la racine �gale au premier �l�ment du seed invers� (c'est-�-dire la derni�re note du pr�fixe d'origine).
        """
        if not self.sequences:
            print("?? Aucun apprentissage disponible, g�n�ration impossible.")
            return []
        
        # On utilise le seed comme la s�quence enregistr�e (seules les hauteurs)
        generated = [note for note, dur in seed]
        # Choix de l'arbre : la racine doit �tre le premier �l�ment du seed invers�
        # Pour la premi�re s�quence [48, 50, 52, 53], le seed devrait �tre [48, 50, 52, 53].
        # La branche correspondante sera construite � partir du pr�fixe [48,50,52] (avec continuation 53)
        # Ainsi, le seed d'entr�e doit �tre trait� comme la s�quence enti�re.
        # On recherche l'arbre dont la racine est le premier �l�ment du pr�fixe invers�, c'est-�-dire:
        # pour le pr�fixe [48,50,52] invers� = [52,50,48], la racine est 52.
        # Ainsi, nous choisissons le root = generated[-1] (la derni�re note) pour g�n�rer la continuation.
        root_note = generated[-1]
        if root_note not in self.roots:
            print("?? Aucun arbre correspondant trouv�, g�n�ration impossible.")
            return []
        node = self.roots[root_note]
        branch = [root_note]
        for _ in range(length):
            if node.child is not None and node.child.continuation is not None:
                next_note = node.child.continuation
                generated.append(next_note)
                branch.append(next_note)
                node = node.child
            else:
                print("?? Fin de la branche, g�n�ration termin�e.")
                break
        print("\n?? **Continuation g�n�r�e**:")
        print("??", " -> ".join(map(str, generated)))
        return generated

    def play_midi_output(self, notes):
        """Simule la lecture MIDI en affichant la s�quence g�n�r�e."""
        print("\n[PLAY MIDI OUTPUT]")
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

    # Simuler un silence
    time.sleep(2)

    # S�quence 2 : [48, 50, 50, 52] (Do, R�, R�, Mi)
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entra�nement avec la s�quence 2 : Do, R�, R�, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)
    continuator.display_memory()
    print("\n=== G�n�ration pour la s�quence 2 ===")
    continuation2 = continuator.generate(sequence2, length=10)
    print("Continuation g�n�r�e :", continuation2)

    # Fin du mode test.
