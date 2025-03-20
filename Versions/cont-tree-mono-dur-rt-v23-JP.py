#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

#hyperparameters

class PrefixTreeNode:
    """
    """
    def __init__(self):
        self.note = None
        self.children = None
        self.continuations = None

class PrefixTreeContinuator:
    """
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

        # Pour k variant de len(notes)-1 � 0 ( du n-1�me �l�ment au premier de la s�quence)
        print('Notes : ' + str(notes) + ' Length notes : ' + str(len(notes)))
#      for k in range(len(notes) - 1, -1 -1):		Does not work correctly ?!!
        k = len(notes) - 1
        while k > 0:
            prefix = notes[:k]         # Sous-s�quence [s1, .. , sN-1]
            cont = notes[k]            # Continuation = sN
            rev_prefix = prefix[::-1]  # Inversion du pr�fixe : [sN-1, ..., s1]
            root_note = rev_prefix[0]  # La racine de cet arbre est sN-1
            print('Parsing k : ' + str(k) + ' rev_prefix : ' + str(rev_prefix) + ' root_note : ' + str(root_note) + ' continuation : ' + str(cont))
            print('V�rification si existe d�j� un arbre de racine : ' + str(root_note))
            # Si cet arbre n'existe pas encore, le cr�er
            if root_note not in self.roots:
                print('Pas trouv� -> Cr�ation arbre de racine : ' + str(root_note) + ' pour sous-s�quence : ' + str(prefix) + ' et continuation : ' + str(cont))
                node = PrefixTreeNode()
                self.roots[root_note] = node
                node.note = root_note
                node.continuations = [cont]
            else:
                print('Un arbre avec racine ' + str(root_note) + ' existe d�j�')
                node = self.roots[root_note]
                node.continuations.append(cont)
  
            # Parcourir rev_prefix (� partir du 2�me �l�ment)
            for note in rev_prefix[1:]:
                print('Parcours sous-s�quence : ' + str(rev_prefix[1:]) + ' pour note : ' + str(note))
                if node.children is None:
                    print('Le noeud parent est sans fils')
                    new_child_node = PrefixTreeNode()
                    new_child_node.note = note
                    new_child_node.continuations = [cont]
                    node.children = [new_child_node]
                    print('Ajout fils : ' + str(note) + ' continuations : ' + str([cont]), end = " ")
                    node = new_child_node
                else:
                    node_exists = False
                    print('Le noeud parent a au moins un fils')
                    print('Recherche parmi les fils si un a pour note : ' + str(note))
                    for child_node in node.children:
                        if child_node.note == note:
                            print('Un fils a pour note : ' + str(note) + ' on lui rajoute la continuation : ' + str(cont))
                            child_node.continuations.append(cont)
                            node_exists = True
                            node = child_node	# on continue � traiter le reste de la s�quence
                            print('On continue � traiter le reste de la s�quence')
                            break
                    if not(node_exists):
                        print('Aucun des fils a pour note : ' + str(note))
                        new_child_node = PrefixTreeNode()
                        print('Cr�ation nouveau fils pour note : ' + str(note) + ' ajout� � la liste des fils du p�re')
                        new_child_node.note = note
                        new_child_node.continuations = [cont]
                        node.children.append(new_child_node)
#                        print('Ajout nouveau fils : ' + str(note) + ' continuations : ' + str([cont]), end = " ")
                        node = new_child_node	# on continue � traiter le reste de la s�quence
            print('')	# Retour � la ligne
            print('On a fini de parser toute la s�quence : ' + str(rev_prefix[1:]))
            print('Dictionnaire arbres : ' + str(self.roots))
            k = k - 1

    def display_memory(self):
        """Affiche l'ensemble des arbres pr�fix�s construits."""
        print("\n?? **Arbres pr�fix�s - M�moire des s�quences enregistr�es**")
        print('Dictionnaire arbres : ' + str(self.roots))
        # Pour chaque arbre, on affiche la branche compl�te avec la continuation
        for root_note, root in self.roots.items():
            print('Visualisation arbre de racine : ' + str(root_note))
            self.print_tree(root)
#            print(f"\n?? Racine : {root_note}")
#            self.display_tree(root, [root_note], level=1)
            print('')	# Retour � la ligne

    def print_tree(self, racine):
        print('Noeud : note : ' + str(racine.note) + ' continuations : ' + str(racine.continuations), end = " ")
        if racine.children != None:
            for child in racine.children:
                self.print_tree(child)
        
    def display_tree(self, node, branch, level):
        print('Display_tree : note : ' + str(node.note) + ' continuations : ' + str(branch))
   #     indent = "    " * level
        # Affichage de la branche actuelle avec la continuation
#        if node.continuation is not None:
#        print(f"{indent}{' -> '.join(map(str, branch))} [ {node.continuations} ]")
#        else:
#            print(f"{indent}{' -> '.join(map(str, branch))}")
        print(str(node.note) + ' [' + str(node.continuations) + ']', end = " ")
#        if node.child is not None:
#            self.display_tree(node.child, branch + [node.child.continuations if node.child.continuations is not None else "?"], level+1)

    def generate(self, played_sequence, max_continuation_length=10):
        """
        """
        if not self.sequences:
            print("There is no tree in the memory with a root note matching last note of the played sequence, thus I cannot generate a continuation.")
            return []
        # Utiliser le seed complet (liste de tuples) pour extraire les notes
        input_sequence = [note for note, dur in played_sequence]
        print('input_sequence : '  + str(input_sequence))
        last_input_note = input_sequence[-1]
        continuations_sequence = []
        print('continuations_sequence : ' + str(continuations_sequence))
        for i in range(2, max_continuation_length):
            if last_input_note not in self.roots:
                print('?? Aucun arbre correspondant trouv� correspondant � note : ' + str(last_input_note) + ' g�n�ration impossible.')
                break
            else:
                print('G�n�ration de la ' + str(i - 1) + '�me note de la continuation � partir de la note : ' + str(last_input_note))
                current_node = self.roots[last_input_note]
                while current_node.children is not None: 		# and node.children.continuation is not None:  Est-ce possible ?
                    print('G�n�ration index i : ' + str(i) + ' noeud : ' + str(current_node) + ' note : ' + str(current_node.note) + ' continuations : ' + str(current_node.continuations))
                    next_child = None
                    for child in current_node.children:		# choisir la branche qui correspond � la prochaine note de la s�quence jou�e si elle existe"
                        print('On cherche un noeud fils du noeud de note : ' + str(current_node.note) + ' avec pour note : ' + str(input_sequence[-i]))
                        if child.note == input_sequence[-i]:
                            next_child = child
                            print('On a trouv� un fils qui a la m�me note : ' + str(child.note))
                            break
                    if next_child == None:		# on n'a pas trouv� la note suivante de la s�quence parmi les fils
                        continuations = current_node.continuations
                        print('Note pas trouv�e parmi les fils. Stop recherche. On tire au sort parmi les continuations du noeud actuel (de note : ' + str(current_node.note) + ') : ' + str(continuations))
                        next_note = continuations[random.randint(0, len(continuations) - 1)]
                        print('G�n�ration nouvelle note de continuation : ' + str(next_note))
                        input_sequence.append(next_note)
                        continuations_sequence.append(next_note)
                        print('continuations_sequence : ' + str(continuations_sequence))
                        last_input_note = next_note # : input_sequence[-1]
                        break
                    else:
                        if len(input_sequence) < i:
                            print('On a �puis� la s�quence d''entr�e')
                            break
                        else:
                            print('On continue la recherche de la pr�c�dente i : ' + str(i) + ' note jou�e de la s�quence : ' + str(input_sequence) + ' parmi les fils')
                            # S'il y en a !!!
                            print('On continue la recherche de la pr�c�dente note jou�e : ' + str(input_sequence[-i]) + ' parmi les fils')
                            current_node = next_child
        print("?? G�n�ration termin�e.")
        print('continuations_sequence : ' + str(continuations_sequence))
        print('Continuation g�n�r�e : ' + str(continuations_sequence))
        return continuations_sequence

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
    continuation1 = continuator.generate(sequence1, max_continuation_length=10)
    print("Continuation g�n�r�e :", continuation1)

    # Simuler un silence (ici, on n'attend pas vraiment, on passe � la s�quence 2)
    time.sleep(2)

    # S�quence 2 : [48, 50, 50, 52] (Do, R�, R�, Mi)
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entra�nement avec la s�quence 2 : Do, R�, R�, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)
    continuator.display_memory()

    print("\n=== G�n�ration pour la s�quence 2 ===")
    continuation2 = continuator.generate(sequence2, max_continuation_length=10)
    print("Continuation g�n�r�e :", continuation2)
    
    # Simuler un silence (ici, on n'attend pas vraiment, on passe � la s�quence 3)
    time.sleep(2)

    # S�quence 3 : [48, 50] (Do, R�)
    sequence3 = [(48, 0.5), (50, 0.5)]
    print("\n=== Entra�nement avec la s�quence 3 : Do, R� (48, 50) ===")
    continuator.train(sequence3)
    continuator.display_memory()

    print("\n=== G�n�ration pour la s�quence 3 ===")
    continuation3 = continuator.generate(sequence3, max_continuation_length=10)
    print("Continuation g�n�r�e :", continuation3)
