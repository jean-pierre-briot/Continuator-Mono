from packaging.tags import PythonVersion

#!/usr/bin/python
# -*- coding: latin-1 -*-

# Continuator in Python
# Version 1.1
# Vanilla version, monophonic, simple state/viewpoint (note only), not considering durations
# 20/02/2025
# Jean-Pierre Briot

# This is a reimplementation of Continuator from François Pachet
# From the informations in his publication:
# Pachet, François, The Continuator: Musical Interaction with Style,
# Proceedings of the International Computer Music Conference 2002,
# Gothenburg, Sweden, September 16-21, 2002, Michigan Publishing.

# Thanks to François for his continuous feedback.

import time
import random
import mido
from mido import MidiFile, open_input, open_output, get_input_names, get_output_names

#hyperparameters
_silence_threshold = 2.0					# Silence duration after which continuator will start train and generate
_max_continuation_length = 10				# Maximum number of notes of a continuation
_max_played_notes_considered = 10		# Maximum last number of played notes considered for training
_default_generated_note_duration = 0.5		# Default duration for generated notes
_default_generated_note_velocity = 64		# Default velocity for generated notes
_after_continuation_sleep = 0.01                	# Sleep duration after having played continuation
_key_transposition_mode = False			# Transposition into 12 keys/tonalities
_octave_transposition_mode = False		# Transposition into all octaves
_real_time_mode = True					# Real-time or Batch mode

class PrefixTreeNode:
    def __init__(self):
        self.note = None
        self.children_list = None
        self.continuation_list = None

class PrefixTreeContinuator:
    def __init__(self):
        self.root_dictionary = {}           # Root tree dictionary
        self.last_note_time = time.time()   # Remembering time start
        self.played_notes = []              # List of played notes events

    def train(self, event_sequence):
                                                                    # event_sequence = [(<pitch_1>, <duration_1>), ... , (<pitch_N>, <duration_N>)]
        note_sequence = [note for note, dummy in event_sequence]    # note_sequence: [<pitch_1>, ... , <pitch_N>]
        self.internal_train(note_sequence)

    def internal_train(self, note_sequence):
        self.internal_train_without_key_transpose(note_sequence)
        if _key_transposition_mode:
            for i in range(1, 12):
                self.internal_train_without_key_transpose(self.transpose(note_sequence, i))

    def internal_train_without_key_transpose(self, note_sequence):
        self.internal_train_without_any_transpose(note_sequence)
        if _octave_transposition_mode:
            max_pitch = max(note_sequence)
            i = 1
            while max_pitch + (i * 12) <= 128:
                self.internal_train_without_any_transpose(self.transpose(note_sequence, i * 12))
                i += 1
            min_pitch = min(note_sequence)
            i = -1
            while min_pitch + (i * 12) >= 0:
                self.internal_train_without_any_transpose(self.transpose(note_sequence, i * 12))
                i += 1
 
    def transpose(self, note_sequence, t):
        transposed_note_sequence = []
        for i in range(0, len(note_sequence)):
            transposed_note_sequence.append(note_sequence[i] + t)
        return(transposed_note_sequence)

    def internal_train_without_any_transpose(self, note_sequence):
        i = len(note_sequence) - 1                                  # index of the last item of the played note sequence
        while i > 0:                                                # Iterative matching of the successive notes (events) of the played sequence
                                                                    # i will vary from length-1 (note_N-1) to 0 (note_1)
         # for k in range(len(note_sequence) - 1, -1 - 1):          Does not work correctly (?), thus substituted by a while loop
            note_sub_sequence = note_sequence[:i]                   # Prefix Sub-sequence: [note_1, .. , note_i]
            continuation = note_sequence[i]                         # Continuation = note_i
            reversed_note_sub_sequence = note_sub_sequence[::-1]    # Reverse Sub-sequence: [note_i, ..., note_1]
            root_note = reversed_note_sub_sequence[0]               # Note of the root of the tree to be created: note_i
            if root_note not in self.root_dictionary:               # If the note has not yet some corresponding prefix tree root,
                current_node = PrefixTreeNode()                     # then, creation of the corresponding new tree (root)
                self.root_dictionary[root_note] = current_node
                current_node.note = root_note
                current_node.continuation_list = [continuation]
            else:                                                   # Otherwise, recursive traversal of the tree branches
                current_node = self.root_dictionary[root_note]
                current_node.continuation_list.append(continuation) # At first, add the continuation to the continuation list of the root
            for note in reversed_note_sub_sequence[1:]:             # Iterative traversal for matching ith level node of the reverse input sequence
                                                                    # with a note of the corresponding ith tree branch level children
                if current_node.children_list is None:              # If there is no children, we have met a terminating leaf,
                    new_child_node = PrefixTreeNode()               # then, we create and insert a new node
                    new_child_node.note = note
                    new_child_node.continuation_list = [continuation]
                    current_node.children_list = [new_child_node]
                    current_node = new_child_node                   # And continue the iterated traversal
                else:                                               # Otherwise
                    node_exists = False                             # Setting up the initial value of a flag to know if we have found a matching node
                    for child_node in current_node.children_list:   # while iterating over the children
                        if child_node.note == note:                 # This child matches
                            child_node.continuation_list.append(continuation)
                            node_exists = True
                            current_node = child_node               # Next iteration will be on the matching process on this child note
                            break                                   # Successful exit from the children iterative search loop
                    if not(node_exists):                            # If no matching node has been found within children,
                        new_child_node = PrefixTreeNode()           # then, we create and insert a new node
                        new_child_node.note = note
                        new_child_node.continuation_list = [continuation]
                        current_node.children_list.append(new_child_node)
                        current_node = new_child_node
            i += -1                                               # Continue the matching search iteration one level down

    def display_memory(self):                                       # To display the list of the trees within the memory
      print('Memory:')
      for root_note, root in self.root_dictionary.items():
         self.display_tree(root, 0)                            # Calling a recursive display of the tree

    def display_tree(self, node, level):                            # Recursive display of a tree nodes (corresponding notes and continuations)
        indent = '  ' * level                                       # Showing number of indentations corresponding to the level of the node
        print(indent, end='')
        print(str(node.note) + str(node.continuation_list))
        if node.children_list != None:
            for child in node.children_list:
                self.display_tree(child, level + 1)

    def generate(self, event_sequence):                             # Generation of a continuation
        note_sequence = [note for note, dur in event_sequence]      # Extract note (pitch) and duration for each event of the sequence
                                                                    # Note sequence : [note_1, .. , note_N]
        length_note_sequence = len(note_sequence)                   # Remember length of the sequence of notes, because will be used iteratively
        last_input_note = note_sequence[-1]                         # We start with the last note of the reverse sequence: Note_N
        continuation_sequence = []                                  # Initialization: Assign continuation list to empty list
        for i in range(1, _max_continuation_length):
            if last_input_note not in self.root_dictionary:         # If there is no matching tree root thus we cannot generate a continuation
                break                                               # thus we exit from loop
            else:                                                   # Otherwise,
                current_node = self.root_dictionary[last_input_note]
                j = 2                                               # Set up j index for a loop for traversing the tree
                                                                    # j is the index of the jth last note of the input sequence
                                                                    # and also the level within the tree
                                                                    # Thus initially, j = 2 : starting with children from the root node to match penultimate note
                while current_node.children_list is not None and j < length_note_sequence:
                                                                    # Iteration to traverse the tree, with at each level (j),
                                                                    # looking for a node matching corresponding note (last jth) of the input sequence
                                                                    # The stop condition is:
                                                                    # a) current node is a leaf (with no children)
                                                                    # or b) j >= length of sequence of notes (i.e. we already parsed all notes of the input sequence)
                    matching_child = None                           # Assign a flag to know if we have found a matching node withing children
                    for child in current_node.children_list:        # Iterate over children nodes to look for a node matching jth last note from input sequence
                        if child.note == note_sequence[-j]:         # If one matches it,
                            matching_child = child                  # then, remember which it is
                            break                                   # and exit from this children iteration loop
                    if matching_child == None:                      # If none of the children matches it,
                        break                                       # then, exit from the traversal to stop the search
                    else:                                           # otherwise, we continue traversing the tree
                        current_node = matching_child               # from current child node
                        j += 1                                   # and down one more level (and previous element of the input sequence)
                if current_node.children_list == None or j >= length_note_sequence or matching_child == None:
                                                                    # If the search is finished
                                                                    # because:
                                                                    # a) we reached a leaf
                                                                    # or b) we reached the end of the reverse sequence
                                                                    # or c) current matching has failed
                                                                    # the, we create a new continuation note
                    current_node_continuation_list = current_node.continuation_list
                    next_note = current_node_continuation_list[random.randint(0, len(current_node_continuation_list) - 1)]
                                                                    # by sorting within current node list of continuations
                                                                    # as there may have several occurrences of the same note,
                                                                    # this implements the probabilities of a Markov model
                    note_sequence.append(next_note) # Add this continuation note to the list of input notes
                    continuation_sequence.append(next_note)         # Add this continuation note to the list of continuations
                    last_input_note = next_note                     # And continue the generation from this (new) last note
        return continuation_sequence

    def play_midi_note_sequence(self, port_name, note_sequence):
        with open_output(port_name) as output:
            for note in note_sequence:
                output.send(mido.Message('note_on', note = note, velocity = _default_generated_note_velocity))
                time.sleep(_default_generated_note_duration)
                output.send(mido.Message('note_off', note = note, velocity = _default_generated_note_velocity))

    def listen_and_continue(self, input_port, output_port):
        with open_input(input_port) as in_port, open_output(output_port) as out_port:
            print('Currently listening on ' + str(input_port))
            while True:                             # Infinite listening loop
                for event in in_port.iter_pending():
                    current_time = time.time()
                    if event.type == 'note_on' and event.velocity > 0:
                        self.played_notes.append((event.note, current_time - self.last_note_time))
                        self.last_note_time = current_time
                    elif event.type == 'note_off':
                        self.last_note_time = current_time
                silence_duration = time.time() - self.last_note_time
                if self.played_notes and silence_duration > _silence_threshold:
                    self.train(self.played_notes)
                    generation_seed_sequence = self.played_notes[-_max_played_notes_considered:]
                    continuation_sequence = self.generate(generation_seed_sequence)
                    if continuation_sequence:
                        self.play_midi_note_sequence(output_port, continuation_sequence)
                    else:
                        print("Generation failed.")
                    self.played_notes = []
                time.sleep(_after_continuation_sleep)

continuator = PrefixTreeContinuator()

if _real_time_mode:
    print('MIDI ports available: ' + str(get_input_names()))  # Display of MIDI ports
    input_port = get_input_names()[0]
    output_port = get_output_names()[0]
    continuator.listen_and_continue(input_port, output_port)
else:           # Batch test
    sequence = [(48, 0.5), (50, 0.5), (52, 0.5), (53, 0.5)]
    print('Training with sequence 1: [C, D, E, F] (48, 50, 52, 53)')
    continuator.train(sequence)
    print('Continuation 1 generated: ' + str(continuator.generate(sequence)))
    sequence = [(48, 0.5), (50, 0.5), (50, 0.5), (52, 0.5)]
    print('Training with sequence 2 : [C, D, D, E] (48, 50, 50, 52)')
    continuator.train(sequence)
    print('Continuation 2 generated: ' + str(continuator.generate(sequence)))
    sequence = [(48, 0.5), (50, 0.5)]
    print('Training with sequence 3 : [C, D] (48, 50)')
    continuator.train(sequence)
    print('Continuation 3 generated: ' + str(continuator.generate(sequence)))
    sequence = [(50, 0.5), (48, 0.5)]
    print('Training with sequence 4 : [D, C] (50, 48)')
    continuator.train(sequence)
    print('Continuation 4 generated: ' + str(continuator.generate(sequence)))
    sequence = [(48, 0.5)]
    print('Training with sequence 5 : [C] (48)')
    continuator.train(sequence)
    print('Generation for sequence_5')
    continuator.train(sequence)
    print('Continuation generated: ' + str(continuator.generate(sequence)))
