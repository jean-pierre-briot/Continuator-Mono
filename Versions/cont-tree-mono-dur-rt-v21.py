#!/usr/bin/python
# -*- coding: latin-1 -*-

import time
import random

# Nous utilisons ici la version monophonique correcte avec arbres pr�fix�s lin�aires.
# Ce code est bas� sur l'algorithme de Fran�ois Pachet.

class PrefixTreeNode:
    """Repr�sente un n�ud dans l'arbre pr�fix� monophonique."""
    def __init__(self):
        self.children = {}
        self.continuation = None  # Une seule continuation pour toute la branche

class PrefixTreeContinuator:
    """
    Continuateur monophonique bas� sur un arbre pr�fix� conforme � la publication de Fran�ois Pachet.
    
    Apr�s l'�coute d'une s�quence, par exemple [48, 50, 52, 53] (Do, R�, Mi, Fa),
    la m�moire doit contenir exactement trois arbres distincts :
        - Racine : 52
            52 -> 50 -> 48 [53]
        - Racine : 50
            50 -> 48 [52]
        - Racine : 48
            48 [50]
    """
    def __init__(self, silence_threshold=2.0):
        self.roots = {}   # Chaque arbre pr�fix� a sa propre racine (cl� = note)
        self.sequences = []  
        self.last_note_time = time.time()
        self.recorded_notes = []  
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Entra�ne l'arbre avec une s�quence (liste de tuples (note, dur�e)).
        On ne consid�re que les hauteurs.
        Pour une s�quence [A, B, C, D], on doit cr�er trois arbres distincts :
            - Arbre de racine C : [C -> B -> A] avec continuation D
            - Arbre de racine B : [B -> A] avec continuation C
            - Arbre de racine A : [A] avec continuation B
        """
        notes = [note for note, dur in sequence]
        self.sequences.append(notes)

        # Pour chaque sous-s�quence d�butant � index 0 et finissant � index (k) (k de 1 � len(notes)-1)
        # on associe la note � l'index k comme continuation.
        for k in range(1, len(notes)):
            # La racine de l'arbre pour cette sous-s�quence est la note � l'index 0
            # mais nous voulons que la structure soit lin�aire � partir du d�but.
            # Selon la publication, pour une s�quence [A, B, C, D] :
            # - l'arbre correspondant � [A] a continuation B,
            # - celui correspondant � [A, B] a continuation C,
            # - celui correspondant � [A, B, C] a continuation D.
            # Ainsi, nous construisons uniquement ces arbres en partant du d�but.
            prefix = notes[:k]  # sous-s�quence de A jusqu'� la note d'index k-1
            continuation = notes[k]  # la note qui suit cette sous-s�quence

            # La racine pour cet arbre sera la premi�re note de la sous-s�quence.
            root_note = prefix[0]
            if root_note not in self.roots:
                self.roots[root_note] = PrefixTreeNode()
            current_node = self.roots[root_note]

            # Construire la branche lin�aire pour cette sous-s�quence
            # On parcourt le pr�fixe du deuxi�me �l�ment � la fin.
            for note in prefix[1:]:
                if note not in current_node.children:
                    current_node.children[note] = PrefixTreeNode()
                current_node = current_node.children[note]

            # Une fois la branche construite, d�finir la continuation unique.
            # Pour �viter les doublons, si une continuation est d�j� d�finie, on la laisse.
            if current_node.continuation is None:
                current_node.continuation = continuation

        print(f"? Arbre mis � jour : {len(self.sequences)} s�quences enregistr�es.")
        self.display_memory()

    def display_memory(self):
        """Affiche la m�moire sous forme d'arbres pr�fix�s distincts, avec indentation pour chaque branche."""
        print("\n?? **Arbres pr�fix�s - M�moire des s�quences enregistr�es**")
        for root_note, root_node in self.roots.items():
            print(f"\n?? Racine : {root_note}")
            self.display_tree(root_node, [root_note], level=1)

    def display_tree(self, node, prefix, level):
        indent = "    " * level
        if node.continuation is not None:
            print(f"{indent}{' -> '.join(map(str, prefix))} [ {node.continuation} ]")
        else:
            print(f"{indent}{' -> '.join(map(str, prefix))}")
        for note, child in node.children.items():
            self.display_tree(child, prefix + [note], level + 1)

    def generate(self, seed, length=10):
        """
        G�n�re une continuation monophonique en se basant sur les arbres pr�fix�s.
        Pour le seed, on utilisera la s�quence enregistr�e.
        """
        if not self.sequences:
            print("?? Aucun apprentissage disponible, g�n�ration impossible.")
            return []

        generated_notes = [note for note, dur in seed]
        # Utiliser la derni�re note du seed pour choisir l'arbre correspondant.
        root_note = generated_notes[0]  # Ici, la racine est la premi�re note du seed.
        if root_note not in self.roots:
            print("?? Aucun arbre correspondant trouv�, g�n�ration impossible.")
            return []

        current_node = self.roots[root_note]
        for _ in range(length):
            if current_node.continuation is not None:
                next_note = current_node.continuation
                generated_notes.append(next_note)
                # Si le prochain_note existe comme enfant, on descend dans l'arbre
                if next_note in current_node.children:
                    current_node = current_node.children[next_note]
                else:
                    break
            else:
                print("?? Fin de la branche, g�n�ration termin�e.")
                break

        print("\n?? **Continuation g�n�r�e**:")
        print("??", " -> ".join(map(str, generated_notes)))
        return generated_notes

    def play_midi_output(self, port_name, notes):
        """Joue une s�quence MIDI monophonique.
           (Ici, on simule simplement l'impression de la s�quence.)
        """
        print("\n[PLAY MIDI OUTPUT]")
        print("Notes jou�es :", " -> ".join(map(str, notes)))
        # Code MIDI r�el (� d�commenter lorsque le clavier sera disponible)
        # with open_output(port_name) as output:
        #     for note in notes:
        #         output.send(mido.Message('note_on', note=note, velocity=64))
        #         time.sleep(0.5)
        #         output.send(mido.Message('note_off', note=note, velocity=64))

    # La partie d'�coute r�elle via MIDI est conserv�e en commentaires :
    # def listen_and_continue(self, input_port, output_port):
    #     with open_input(input_port) as inport, open_output(output_port) as outport:
    #         print(f"?? �coute en cours sur : {input_port}")
    #         while True:
    #             for msg in inport.iter_pending():
    #                 current_time = time.time()
    #                 if msg.type == 'note_on' and msg.velocity > 0:
    #                     self.recorded_notes.append((msg.note, current_time - self.last_note_time))
    #                     self.last_note_time = current_time
    #                 elif msg.type == 'note_off':
    #                     self.last_note_time = current_time
    #
    #             silence_duration = time.time() - self.last_note_time
    #             if self.recorded_notes and silence_duration > self.silence_threshold:
    #                 print("?? Silence d�tect�, g�n�ration de la continuation...")
    #                 self.train(self.recorded_notes)
    #                 seed = self.recorded_notes[-2:]
    #                 generated_sequence = self.generate(seed, length=10)
    #                 if generated_sequence:
    #                     self.play_midi_output(output_port, generated_sequence)
    #                 else:
    #                     print("?? �chec de la g�n�ration, pas assez de donn�es.")
    #                 self.recorded_notes = []
    #             time.sleep(0.01)

# ------------------- Test Mode -------------------
if __name__ == '__main__':
    # Cr�ation du continuateur
    continuator = PrefixTreeContinuator(silence_threshold=2.0)

    # S�quence 1 : [48, 50, 52, 53] correspond � Do, R�, Mi, Fa.
    sequence1 = [(48, 0.5), (50, 0.5), (52, 0.5), (53, 0.5)]
    print("=== Entra�nement avec la s�quence 1 : Do, R�, Mi, Fa (48, 50, 52, 53) ===")
    continuator.train(sequence1)

    # On affiche la m�moire des arbres pr�fix�s
    continuator.display_memory()

    # G�n�ration de la continuation pour la s�quence 1
    print("\n=== G�n�ration de la continuation pour la s�quence 1 ===")
    continuation1 = continuator.generate(sequence1, length=10)
    print("Continuation g�n�r�e :", continuation1)

    # Simuler un silence et une deuxi�me s�quence.
    time.sleep(2)  # Simuler le silence

    # S�quence 2 : [48, 50, 50, 52] correspond � Do, R�, R�, Mi.
    sequence2 = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print("\n=== Entra�nement avec la s�quence 2 : Do, R�, R�, Mi (48, 50, 50, 52) ===")
    continuator.train(sequence2)

    # Affichage mis � jour de la m�moire
    continuator.display_memory()

    # G�n�ration de la continuation pour la s�quence 2
    print("\n=== G�n�ration de la continuation pour la s�quence 2 ===")
    continuation2 = continuator.generate(sequence2, length=10)
    print("Continuation g�n�r�e :", continuation2)

    # Fin du mode test.
