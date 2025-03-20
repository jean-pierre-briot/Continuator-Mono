document.addEventListener("DOMContentLoaded", async () => {
    if (!navigator.requestMIDIAccess) {
        console.log("Web MIDI API non support�e");
        return;
    }

    try {
        const midiAccess = await navigator.requestMIDIAccess();
        const inputs = Array.from(midiAccess.inputs.values());
        const outputs = Array.from(midiAccess.outputs.values());

        if (inputs.length === 0 || outputs.length === 0) {
            console.log("Aucune entr�e ou sortie MIDI d�tect�e");
            return;
        }

        const input = inputs[1]; // Premi�re entr�e MIDI
        const output = outputs[0]; // Premi�re sortie MIDI

        console.log(`Utilisation de l'entr�e: ${input.name}`);
        console.log(`Utilisation de la sortie: ${output.name}`);

        let melody = [];
        let activeNotes = new Set();
        let playedNotes = new Map(); // Utilisation d'une Map pour suivre les notes jou�es et leur statut
        let lastNoteTime = 0;
        const silenceThreshold = 1000; // 1 seconde en ms
        let playbackTimeout = null;
        let playbackActive = false;
        let playbackTimers = [];

        input.onmidimessage = (event) => {
            const [status, note, velocity] = event.data;
            const currentTime = performance.now();

            if (playbackTimeout) {
                clearTimeout(playbackTimeout);
            }

            if (playbackActive) {
                stopPlayback();
            }

            if (status >= 144 && status < 160 && velocity > 0) { // Note On
                activeNotes.add(note);
                melody.push([status, note, velocity, currentTime]);
            } else if (status >= 128 && status < 160) { // Note Off
                activeNotes.delete(note);
                melody.push([status, note, velocity, currentTime]);
            }

            lastNoteTime = currentTime;

            playbackTimeout = setTimeout(checkAndPlayMelody, silenceThreshold);
        };

        function checkAndPlayMelody() {
            if (melody.length === 0 || activeNotes.size > 0) return;
            playTransposedMelody();
        }

        function playTransposedMelody() {
            console.log("Rejoue la m�lodie transpos�e...");
            const startTime = melody[0][3];
            playbackActive = true;
            playedNotes.clear();

            melody.forEach(([status, note, velocity, time]) => {
                const delay = time - startTime;
                const transposedNote = note + 2;

                const timer = setTimeout(() => {
                    output.send([status, transposedNote, velocity]);
                    if (status >= 144 && status < 160 && velocity > 0) {
                        playedNotes.set(transposedNote, status); // Stocker la note jou�e avec son statut
                    } else if (status >= 128 && status < 160) {
                        playedNotes.delete(transposedNote); // Retirer la note si elle est arr�t�e
                    }
                }, delay);
                playbackTimers.push(timer);
            });
            melody = []
        }

        function stopPlayback() {
            console.log("Arr�t de la lecture en cours");
            playbackTimers.forEach(clearTimeout);
            playbackTimers = [];
            playbackActive = false;

            // Envoyer les Note Off pour toutes les notes jou�es qui n'ont pas encore �t� arr�t�es
            playedNotes.forEach((status, note) => {
                if (status >= 144 && status < 160) { // Si une Note On est active
                    output.send([128, note, 0]); // Envoyer un Note Off
                }
            });
            playedNotes.clear();
        }
    } catch (error) {
        console.error("Erreur d'acc�s au MIDI: ", error);
    }
});