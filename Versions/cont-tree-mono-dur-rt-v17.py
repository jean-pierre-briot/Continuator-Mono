#!/usr/bin/python
# -*- coding: latin-1 -*-

import mido
import time
import random
from mido import open_input, open_output, get_input_names, get_output_names

class PrefixTreeNode:
    """Repr�sente un n�ud dans l'arbre pr�fix� monophonique."""
    def __init__(self):
        self.children = {}
        self.continuations = []  # Liste des notes de continuation

class PrefixTreeContinuator:
    """Continuateur monophonique bas� sur un arbre pr�fix� conforme � la publication de Fran�ois Pachet."""
    def __init__(self, silence_threshold=2.0):
        self.roots = {}  # Chaque arbre pr�fix� a sa propre racine
        self.sequences = []  
        self.last_note_time = time.time()
        self.recorded_notes = []  
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """
        Ajoute une s�quence � l'arbre pr�fix� en conservant des arbres distincts.
        Chaque s�quence m�moris�e a une racine qui correspond � sa derni�re note.
        """
        notes = [note[0] for note in sequence]  
        self.sequences.append(notes)

        # D�finir la racine de l'arbre correspondant � la derni�re note
        root_note = notes[-1]
        if root_note not in self.roots:
            self.roots[root_note] = PrefixTreeNode()
        current_node = self.roots[root_note]

        # Construire l'arbre pr�fix� sp�cifique � cette s�quence
        for i in range(len(notes) - 2, -1, -1):  
            note = notes[i]
            if note not in current_node.children:
                current_node.children[note] = PrefixTreeNode()
            current_node = current_node.children[note]

        # Ajouter la continuation (prochaine note apr�s ce pr�fixe)
        if len(notes) > 1 and notes[-1] not in current_node.continuations:
            current_node.continuations.append(notes[-1])

        print(f"? Arbre mis � jour : {len(self.sequences)} s�quences enregistr�es.")
        self.display_memory()

    def display_memory(self):
        """Affiche une repr�sentation de l?ensemble des arbres pr�fix�s de mani�re distincte."""
        print("\n?? **Arbres pr�fix�s - M�moire des s�quences enregistr�es**")
        for root_note, root_node in self.roots.items():
            print(f"\n?? Racine : {root_note}")
            self.display_tree(root_node, [root_note], level=1)

    def display_tree(self, node, prefix, level):
        """Affiche un arbre pr�fix� sp�cifique avec indentation pour chaque niveau."""
        for note, child in node.children.items():
            indent = "    " * level
            print(f"{indent}{' -> '.join(map(str, prefix + [note]))}  | Continuations: {child.continuations}")
            self.display_tree(child, prefix + [note], level + 1)

    def generate(self, seed, length=10):
        """G�n�re une continuation monophonique en parcourant les arbres pr�fix�s."""
        if not self.sequences:
            print("?? Aucun apprentissage disponible, g�n�ration impossible.")
            return []

        generated_notes = [note[0] for note in seed]
        root_note = generated_notes[-1]

        if root_note not in self.roots:
            print("?? Aucun arbre correspondant trouv�, g�n�ration impossible.")
            return []

        current_node = self.roots[root_note]

        for _ in range(length):
            match_found = False
            for i in range(len(generated_notes), 0, -1):
                sub_prefix = generated_notes[-i:]
                temp_node = current_node
                valid = True
                for note in sub_prefix:
                    if note in temp_node.children:
                        temp_node = temp_node.children[note]
                    else:
                        valid = False
                        break
                if valid and temp_node.continuations:
                    next_note = random.choice(temp_node.continuations)
                    generated_notes.append(next_note)
                    match_found = True
                    break
            if not match_found:
                print("?? Aucun pr�fixe exact trouv�, fin de la g�n�ration.")
                break

        print("\n?? **Continuation g�n�r�e**:")
        print("??", " -> ".join(map(str, generated_notes)))
        return generated_notes

    def play_midi_output(self, port_name, notes):
        """Joue une s�quence MIDI monophonique."""
        with open_output(port_name) as output:
            for note in notes:
                output.send(mido.Message('note_on', note=note, velocity=64))
                time.sleep(0.5)  
                output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """�coute le flux MIDI et g�n�re une continuation apr�s un silence."""
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"?? �coute en cours sur : {input_port}")
            while True:
                for msg in inport.iter_pending():
                    current_time = time.time()
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.recorded_notes.append((msg.note, current_time - self.last_note_time))
                        self.last_note_time = current_time
                    elif msg.type == 'note_off':
                        self.last_note_time = current_time

                silence_duration = time.time() - self.last_note_time
                if self.recorded_notes and silence_duration > self.silence_threshold:
                    print("?? Silence d�tect�, g�n�ration de la continuation...")
                    self.train(self.recorded_notes)
                    seed = self.recorded_notes[-2:]  
                    generated_sequence = self.generate(seed, length=10)
                    if generated_sequence:
                        self.play_midi_output(output_port, generated_sequence)
                    else:
                        print("?? �chec de la g�n�ration, pas assez de donn�es.")
                    self.recorded_notes = []
                time.sleep(0.01)

# Affichage et s�lection des ports MIDI
print("?? Ports MIDI disponibles :", get_input_names())
input_port = get_input_names()[0]
output_port = get_output_names()[0]

# Lancement du continuateur monophonique
continuator = PrefixTreeContinuator(silence_threshold=2.0)
continuator.listen_and_continue(input_port, output_port)
