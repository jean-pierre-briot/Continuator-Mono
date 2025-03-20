#!/usr/bin/python
# -*- coding: latin-1 -*-

# python3 -m pip install python-rtmidi

import mido
import time
import random
from collections import defaultdict
from mido import open_input, open_output, get_input_names, get_output_names

#_note_default_duration = 250
_max_generated_notes = 10
_duration_from_learned = False 	# duration from learned notes (or from played notes)

class PrefixTreeNode:
    """Repr�sente un n�ud dans l'arbre pr�fix� (stocke des accords tri�s)."""
    def __init__(self):
        self.children = {}
        self.continuations = []

class PrefixTreeContinuatorRealtime:
    """Continuateur en temps r�el bas� sur un arbre pr�fix�, avec support de la polyphonie."""
    def __init__(self, silence_threshold=2.0, duration_from_learned=_duration_from_learned):
        self.root = PrefixTreeNode()
        self.sequences = []
        self.durations = []
        self.last_note_time = time.time()
        self.recorded_notes = []
        self.active_notes = set()  # Notes actuellement press�es
        self.silence_threshold = silence_threshold
        self.duration_from_learned = duration_from_learned  

        # ?? S�quence d?amor�age pour �viter un arbre vide au d�part
        self.train([((60, 64, 67), 0.3)])  # Un accord de do majeur

    def train(self, sequence):
        """Ajoute une s�quence � l'arbre pr�fix� en ignorant les dur�es pour la structure."""
        seq_index = len(self.sequences)
        chords = [tuple(sorted(note[0])) for note in sequence]  # Normalisation des accords
        durations = [note[1] for note in sequence]

        self.sequences.append(chords)
        self.durations.append(durations)

        for start in range(len(chords)):
            current_node = self.root
            for i in range(len(chords) - 1, start - 1, -1):
                chord = chords[i]
                if chord not in current_node.children:
                    current_node.children[chord] = PrefixTreeNode()
                current_node = current_node.children[chord]

                if seq_index not in current_node.continuations:
                    current_node.continuations.append(seq_index)

        print(f"Arbre mis � jour : {len(self.sequences)} s�quences enregistr�es.")

    def generate(self, seed, length=10):
        """G�n�re une continuation polyphonique."""
        if not self.sequences:
            print("Aucun apprentissage disponible, g�n�ration impossible.")
            return []

        generated_chords = [tuple(sorted(note[0])) for note in seed]

        for _ in range(length):
            current_node = self.root
            match_found = False
            i = len(generated_chords) - 1

            # ?? Recherche du pr�fixe le plus long
            while i >= 0:
                chord = generated_chords[i]
                if chord in current_node.children:
                    current_node = current_node.children[chord]
                    match_found = True
                else:
                    break
                i -= 1

            # ? S�lection d'une continuation si possible
            if match_found and current_node.continuations:
                seq_index = random.choice(current_node.continuations)
            else:
                print("Aucun pr�fixe exact trouv�, choix d'une s�quence existante.")
                seq_index = random.randint(0, len(self.sequences) - 1)

            next_pos = len(generated_chords) % len(self.sequences[seq_index])
            next_chord = self.sequences[seq_index][next_pos]
            generated_chords.append(next_chord)

        # ?? R�assignation des dur�es
        generated_sequence = []
        for i, chord in enumerate(generated_chords):
            if self.duration_from_learned:
                seq_index = random.choice(current_node.continuations) if current_node.continuations else 0
                duration = self.durations[seq_index][i % len(self.durations[seq_index])]
            else:
                duration = seed[i % len(seed)][1] if i < len(seed) else 0.3

            generated_sequence.append((chord, duration))

        return generated_sequence

    def play_midi_output(self, port_name, chords):
        """Joue une s�quence MIDI polyphonique."""
        with open_output(port_name) as output:
            for chord, duration in chords:
                for note in chord:
                    output.send(mido.Message('note_on', note=note, velocity=64))
                time.sleep(duration)
                for note in chord:
                    output.send(mido.Message('note_off', note=note, velocity=64))

    def listen_and_continue(self, input_port, output_port):
        """�coute le flux MIDI et g�n�re une continuation apr�s un silence."""
        with open_input(input_port) as inport, open_output(output_port) as outport:
            print(f"�coute en cours sur : {input_port}")

            while True:
                for msg in inport.iter_pending():
                    current_time = time.time()
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.active_notes.add(msg.note)
                        self.last_note_time = current_time

                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        self.active_notes.discard(msg.note)
                        self.last_note_time = current_time

                    if not self.active_notes and self.recorded_notes:
                        duration = current_time - self.last_note_time
                        sorted_chord = tuple(sorted(self.recorded_notes[-1][0]))  # Normalisation
                        self.recorded_notes.append((sorted_chord, duration))

                # ?? G�n�ration de continuation apr�s un silence
                if self.recorded_notes and (time.time() - self.last_note_time > self.silence_threshold):
                    print("Silence d�tect�, g�n�ration de la continuation...")
                    self.train(self.recorded_notes)  
                    seed = self.recorded_notes[-2:]  
                    generated_sequence = self.generate(seed, length=10)

                    if generated_sequence:
                        self.play_midi_output(output_port, generated_sequence)
                    else:
                        print("�chec de la g�n�ration, pas assez de donn�es.")

                    self.recorded_notes = []  

                time.sleep(0.01)  

# ?? Affichage des ports MIDI disponibles
print("Ports MIDI disponibles :", get_input_names())

# ?? S�lection automatique des ports MIDI
input_port = get_input_names()[0]
output_port = get_output_names()[0]

# ?? Lancement du continuateur polyphonique
continuator = PrefixTreeContinuatorRealtime(duration_from_learned=_duration_from_learned)  
continuator.listen_and_continue(input_port, output_port)
