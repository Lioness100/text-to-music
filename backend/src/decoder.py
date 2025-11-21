from typing import List, Tuple
import mido

from .phoneme_mapping import IPA_TO_MUSIC


def read_midi_file(midi_file: str) -> List[Tuple[int, float, int]]:
    midi = mido.MidiFile(midi_file)

    melody_track = None
    for track in midi.tracks:
        track_name = ""
        for msg in track:
            if msg.type == "track_name":
                track_name = msg.name
                break

        if "Melody" in track_name or "Data" in track_name:
            melody_track = track
            break

        if melody_track is None:
            has_notes = any(msg.type == "note_on" and msg.velocity > 0 for msg in track)
            if has_notes:
                melody_track = track

    notes = []
    if melody_track:
        current_time = 0
        active_notes = {}

        for msg in melody_track:
            current_time += msg.time

            if msg.type == "note_on" and msg.velocity > 0:
                active_notes[msg.note] = (current_time, msg.velocity)
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                if msg.note in active_notes:
                    start_time, velocity = active_notes[msg.note]
                    duration = current_time - start_time
                    duration_beats = duration / midi.ticks_per_beat
                    notes.append((msg.note, duration_beats, velocity))
                    del active_notes[msg.note]

    return notes


def decode_music_to_text(
    midi_notes: List[Tuple[int, float, int]], reverse_cmu: dict
) -> str:
    MUSIC_TO_IPA = {v: k for k, v in IPA_TO_MUSIC.items()}

    filtered_notes = midi_notes[4:-4]

    ipa_phonemes = []
    for pitch, duration, velocity in filtered_notes:
        if pitch == 24 and velocity <= 2:
            ipa_phonemes.append(" ")
            continue

        best_match = None
        best_distance = float("inf")

        for (ref_pitch, ref_dur, ref_vel), phoneme in MUSIC_TO_IPA.items():
            possible_durations = [ref_dur, ref_dur * 1.2, ref_dur * 0.9]
            dur_distance = min(abs(duration - d) for d in possible_durations)

            distance = (
                abs(pitch - ref_pitch) * 10
                + abs(velocity - ref_vel) * 0.5
                + dur_distance * 1
            )

            if distance < best_distance:
                best_distance = distance
                best_match = phoneme

        if best_match:
            ipa_phonemes.append(best_match)

    ipa_string = "".join(ipa_phonemes)
    ipa_words = ipa_string.split(" ")

    decoded_words = [
        reverse_cmu.get(ipa_word, ipa_word) for ipa_word in ipa_words if ipa_word
    ]

    return " ".join(decoded_words)


def decode_midi_file(midi_file: str, reverse_cmu: dict) -> str:
    notes = read_midi_file(midi_file)
    return decode_music_to_text(notes, reverse_cmu)
