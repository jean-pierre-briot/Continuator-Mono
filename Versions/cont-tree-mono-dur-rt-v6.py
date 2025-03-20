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
        self.continuation = None  # Une seule note en continuation (au lieu d'une liste)

class PrefixTreeContinuator:
    """Continuateur monophonique bas� sur un arbre pr�fix� fid�le � la publication de Fran�ois Pachet."""
    def __init__(self, silence_threshold=2.0):
        self.root = PrefixTreeNode()
        self.sequences = []
        self.last_note_time = time.time()
        self.recorded_notes = []
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """Ajoute une s�quence � l'arbre pr�fix� comme d�crit dans la publication."""
        seq_index = len(self.sequences)
        self.sequences.append(sequence)

        for start in range(len(sequence)):
            current_node = self.root
            for i in range(len(sequence) - 1, start - 1, -1):
                note = sequence[i]
                if note not in current_node.children:
                    current_node.children[note] = PrefixTreeNode()
                current_node = current_node.children[note]

                # La continuation est toujours UNE seule note (la suivante dans la s�quence)
                if i < len(sequence) - 1:
                    current_node.continuation = sequence[i + 1]

        print(f"? Arbre mis � jour : {len(self.sequences)} s�quences enregistr�es.")
        self.display_memory()

    def display_memory(self, node=None, prefix=[]):
        """Affiche une repr�sentation de l?arbre pr�fix� monophonique."""
        if node is None:
            node = self.root
            print("\n?? **Arbre pr�fix� - M�moire des s�quences enregistr�es**")

        for note, child_node in node.children.items():
            continuation_note = child_node.continuation if child_node.continuation else "?"
            print(f"{' -> '.join(map(str, prefix + [note]))}  | Continuation: {continuation_note}")
            self.display_memory(child_node, prefix + [note])

    def generate(self, seed, length=10):
        """G�n�re une continuation monophonique en suivant l?arbre pr�fix�."""
        if not self.sequences:
            print("?? Aucun apprentissage disponible, g�n�ration impossible.")
            return []

        generated_notes = list(seed)

        for _ in range(length):
            current_node = self.root
            match_found = False
            i = len(generated_notes)

            while i > 0:
                sub_prefix = generated_notes[-i:]  
                temp_node = self.root
                match_found = True
                for note in sub_prefix:
                    if note in temp_node.children:
                        temp_node = temp_node.children[note]
                    else:
                        match_found = False
                        break

                if match_found and temp_node.continuation:
                    generated_notes.append(temp_node.continuation)
                    break  
                i -= 1  

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
                time.sleep(0.5)  # Dur�e fixe pour l?instant
                output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """�coute le flux MIDI et g�n�re une continuation apr�s un silence."""
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"?? �coute en cours sur : {input_port}")

            while True:
                for msg in inport.iter_pending():
                    current_time = time.time()

                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.recorded_notes.append(msg.note)
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

print("?? Ports MIDI disponibles :", get_input_names())
input_port = get_input_names()[0]
output_port = get_output_names()[0]

continuator = PrefixTreeContinuator(silence_threshold=2.0)  
continuator.listen_and_continue(input_port, output_port)
