import os
from datetime import datetime
from typing import List, Tuple
from music21 import stream, note, chord, tempo, instrument, meter

from .phoneme_mapping import IPA_TO_MUSIC
from .dictionary import text_to_ipa, ipa_to_phonemes


def ipa_to_notes(ipa_string: str) -> List[Tuple[int, float, int]]:
    phonemes = ipa_to_phonemes(ipa_string)
    notes = []

    for phoneme in phonemes:
        if phoneme == " ":
            notes.append(IPA_TO_MUSIC[" "])
            continue

        phoneme_clean = phoneme.replace("ˈ", "").replace("ˌ", "")

        if phoneme_clean in IPA_TO_MUSIC:
            notes.append(IPA_TO_MUSIC[phoneme_clean])
        else:
            notes.append((60, 0.4, 80))

    return notes


def create_melody_stream(notes: List[Tuple[int, float, int]]) -> stream.Part:
    melody = stream.Part()
    melody.insert(0, instrument.Piano())
    melody.insert(0, tempo.MetronomeMark(number=120))
    melody.insert(0, meter.TimeSignature("4/4"))

    # Intro arpeggio
    if notes:
        first_pitch = notes[0][0]
        root = (first_pitch % 12) + 48
        intro_notes = [root, root + 4, root + 7, root + 12]
        for pitch in intro_notes:
            n = note.Note(pitch, quarterLength=0.5)
            n.volume.velocity = 70
            melody.append(n)

    # Main melody
    for i, (pitch, duration, velocity) in enumerate(notes):
        # Rhythmic variation
        if i % 4 == 0:
            duration *= 1.2
        elif i % 4 == 2:
            duration *= 0.9

        n = note.Note(pitch, quarterLength=duration)
        n.volume.velocity = velocity
        melody.append(n)

    # Outro arpeggio
    if notes:
        last_pitch = notes[-1][0]
        root = (last_pitch % 12) + 60
        outro_notes = [root + 12, root + 7, root + 4, root]
        for pitch in outro_notes:
            n = note.Note(pitch, quarterLength=0.5)
            n.volume.velocity = 70
            melody.append(n)

    return melody


def create_bass_stream(melody: stream.Part) -> stream.Part:
    bass = stream.Part()
    bass.insert(0, instrument.AcousticBass())

    measure_duration = 2.0
    current_offset = 0
    melody_duration = melody.duration.quarterLength

    while current_offset < melody_duration:
        window_notes = (
            melody.flatten()
            .getElementsByOffset(
                current_offset,
                current_offset + measure_duration,
                includeEndBoundary=False,
                mustFinishInSpan=False,
            )
            .notes
        )

        if window_notes:
            # Use first note's pitch class for bass
            pitch_class = window_notes[0].pitch.pitchClass
            bass_pitch = 36 + pitch_class  # C2 register
        else:
            bass_pitch = 36

        n = note.Note(bass_pitch, quarterLength=measure_duration)
        n.volume.velocity = 75
        bass.append(n)
        current_offset += measure_duration

    return bass


def create_harmony_stream(melody: stream.Part) -> stream.Part:
    strings = stream.Part()
    strings.insert(0, instrument.StringInstrument())

    chord_duration = 3.0
    current_offset = 0
    melody_duration = melody.duration.quarterLength

    while current_offset < melody_duration:
        window_notes = (
            melody.flatten()
            .getElementsByOffset(
                current_offset,
                current_offset + chord_duration,
                includeEndBoundary=False,
                mustFinishInSpan=False,
            )
            .notes
        )

        if window_notes:
            # Build major triad from first note
            root = window_notes[0].pitch.pitchClass
            chord_pitches = [48 + root, 48 + (root + 4) % 12, 48 + (root + 7) % 12]
        else:
            chord_pitches = [48, 52, 55]  # C major

        c = chord.Chord(chord_pitches, quarterLength=chord_duration)
        c.volume.velocity = 55
        strings.append(c)
        current_offset += chord_duration

    return strings


def create_pad_stream(melody: stream.Part) -> stream.Part:
    pad = stream.Part()
    pad.insert(0, instrument.Instrument())
    pad.instrumentName = "Pad"

    pad_duration = 6.0
    current_offset = 0
    melody_duration = melody.duration.quarterLength

    while current_offset < melody_duration:
        window_notes = (
            melody.flatten()
            .getElementsByOffset(
                current_offset,
                current_offset + pad_duration,
                includeEndBoundary=False,
                mustFinishInSpan=False,
            )
            .notes
        )

        if window_notes:
            root = 36 + window_notes[0].pitch.pitchClass
        else:
            root = 36

        c = chord.Chord([root, root + 7], quarterLength=pad_duration)
        c.volume.velocity = 40
        pad.append(c)
        current_offset += pad_duration

    return pad


def encode_text_to_music(text: str, cmu_dict: dict):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("outputs", f"encoded_music_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    midi_output = os.path.join(output_dir, "encoded_music.mid")

    ipa = text_to_ipa(text, cmu_dict)
    notes = ipa_to_notes(ipa)

    score = stream.Score()
    melody = create_melody_stream(notes)
    score.append(melody)
    score.append(create_bass_stream(melody))
    score.append(create_harmony_stream(melody))
    score.append(create_pad_stream(melody))
    score.write("midi", fp=midi_output)

    melody_notes = [
        (
            n.pitch.midi,
            float(n.duration.quarterLength),
            n.volume.velocity,
        )
        for n in melody.flatten().notes
    ]

    return ipa, melody_notes, midi_output
