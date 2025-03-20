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
        self.continuations = []  # Liste de notes individuelles servant de continuation

class PrefixTreeContinuator:
    """Continuateur monophonique bas� sur un arbre pr�fix� fid�le � la publication de Fran�ois Pachet."""
    def __init__(self, silence_threshold=2.0):
        self.root = PrefixTreeNode()
        self.sequences = []
        self.durations = []
        self.last_note_time = time.time()
        self.recorded_notes = []
        self.silence_threshold = silence_threshold

    def train(self, sequence):
        """Ajoute une s�quence � l'arbre pr�fix� en suivant la structure correcte (CBA, BA, A)."""
        seq_index = len(self.sequences)
        notes = [note[0] for note in sequence]  # Extraire uniquement les hauteurs
        durations = [note[1] for note in sequence]  # Extraire uniquement les dur�es

        self.sequences.append(notes)
        self.durations.append(durations)

        for start in range(len(notes) - 1, -1, -1):  # Lecture de droite � gauche
            current_node = self.root
            for i in range(start, -1, -1):
                note = notes[i]
                if note not in current_node.children:
                    current_node.children[note] = PrefixTreeNode()
                current_node = current_node.children[note]

                # Ajout de la continuation (note suivante)
                if start < len(notes) - 1 and notes[start + 1] not in current_node.continuations:
                    current_node.continuations.append(notes[start + 1])

        print(f"? Arbre mis � jour : {len(self.sequences)} s�quences enregistr�es.")
        self.display_memory()

    def display_memory(self, node=None, prefix=[]):
        """Affiche une repr�sentation de l?arbre pr�fix� monophonique."""
        if node is None:
            node = self.root
            print("\n?? **Arbre pr�fix� - M�moire des s�quences enregistr�es**")

        for note, child_node in node.children.items():
            print(f"{' -> '.join(map(str, prefix + [note]))}  | Continuations: {child_node.continuations}")
            self.display_memory(child_node, prefix + [note])

    def generate(self, seed, length=10):
        """G�n�re une continuation monophonique avec gestion correcte des dur�es."""
        if not self.sequences:
            print("?? Aucun apprentissage disponible, g�n�ration impossible.")
            return []

        generated_notes = [note[0] for note in seed]
        generated_durations = [note[1] for note in seed]

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

                if match_found and temp_node.continuations:
                    next_note = random.choice(temp_node.continuations)
                    generated_notes.append(next_note)
                    break  
                i -= 1  

            if not match_found:
                print("?? Aucun pr�fixe exact trouv�, fin de la g�n�ration.")
                break

            # Gestion des dur�es : r�utilisation des dur�es apprises
            seq_index = random.randint(0, len(self.sequences) - 1)
            next_duration = self.durations[seq_index][len(generated_notes) % len(self.durations[seq_index])]
            generated_durations.append(next_duration)

        generated_sequence = list(zip(generated_notes, generated_durations))

        print("\n?? **Continuation g�n�r�e**:")
        for note, duration in generated_sequence:
            print(f"?? {note} (Dur�e: {duration:.3f}s)")

        return generated_sequence

    def play_midi_output(self, port_name, notes):
        """Joue une s�quence MIDI monophonique avec gestion du rythme."""
        with open_output(port_name) as output:
            for note, duration in notes:
                output.send(mido.Message('note_on', note=note, velocity=64))
                time.sleep(duration)  # Utilisation des dur�es apprises
                output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """�coute le flux MIDI et g�n�re une continuation apr�s un silence."""
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"?? �coute en cours sur : {input_port}")

            while True:
                for msg in inport.iter_pending():
                    current_time = time.time()

                    if msg.type == 'note_on' and msg.velocity > 0:
                        duration = current_time - self.last_note_time
                        self.recorded_notes.append((msg.note, duration))
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
