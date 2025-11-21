# Text to Music Encoder/Decoder

![Demo](https://i.imgur.com/V9HHsuK.png)

A web application that converts text to music and back by mapping phonemes to MIDI parameters.

## How It Works

Text is converted to music through a multi-stage pipeline that transforms linguistic information into MIDI parameters.

### Encoding Process

**Stage 1: Text to Phonemes**

Input text is converted to International Phonetic Alphabet (IPA) symbols using the CMU Pronouncing Dictionary. Each word is looked up and converted to its phonetic representation. Words not in the dictionary are spelled phonetically. Stress markers indicate syllable emphasis.

**Stage 2: Phoneme to MIDI Mapping**

Each IPA phoneme maps to three MIDI parameters: pitch (note height), duration (note length), and velocity (loudness). The mapping is based on phonetic features.

***Consonants***

Voiceless stops (p, t, k) map to C major scale notes with short duration (0.3-0.4 beats) and high velocity (100). Voiced stops (b, d, g) use lower octaves with slightly longer duration (0.4 beats) and reduced velocity (90). Fricatives (f, v, s, z, sh, th) occupy higher registers with medium duration (0.4-0.5 beats) and moderate velocity (70-85). Nasals (m, n, ng) use mid-range pitches with longer duration (0.6 beats) and strong velocity (95). Liquids (l, r) flow smoothly with medium duration (0.5 beats) and velocity (90).

***Vowels***

High vowels (i, u) map to high pitches (G5-A5) with sustained duration (0.6 beats) and full velocity (100). Mid vowels (e, o, schwa) occupy middle registers (A4-D5) with medium-long duration (0.5-0.6 beats). Low vowels (a, æ) use lower pitches (D4-F4) with full duration (0.6 beats) and maximum velocity (100). Diphthongs extend slightly longer (0.7 beats) to accommodate the vowel transition.

***Special Cases***

Spaces between words are encoded as very low pitch (C1, MIDI 24) with minimal velocity (1), creating a barely audible marker. This preserves word boundaries without silence gaps. An intro sequence of four ascending notes precedes the message. An outro sequence of four descending notes follows. Both use 0.4 beat duration at velocity 80.

**Stage 3: MIDI Generation**

Phoneme-to-MIDI mappings are written to a standard MIDI file format using multiple tracks. Track 0 contains the melody (encoded phonemes). Track 1 provides bass accompaniment. Track 2 adds harmonic strings. Track 3 includes atmospheric pad. Tempo is set at 120 BPM with 4/4 time signature.

### Decoding Process

MIDI files are decoded by reversing the encoding pipeline. Notes are extracted from the melody track. Intro and outro sequences are filtered. Each note's pitch, duration, and velocity are compared against the phoneme mapping table. The closest match is selected using weighted distance calculation: pitch difference multiplied by 10, velocity difference multiplied by 0.5, duration difference multiplied by 1. Space markers (pitch 24, velocity 1-2) restore word boundaries. Phoneme sequences are matched against the CMU dictionary to reconstruct words. The longest matching phoneme sequence is selected when multiple words share pronunciations.

### Limitations

Homophone ambiguity occurs when different words share identical pronunciations. The decoder returns the first dictionary match. Dictionary coverage is limited to CMU entries. Pronunciation variants exist for many words. MIDI quantization limits temporal precision. Velocity and duration tolerances allow approximate matching during decode.

## Installation

Install Python dependencies:

```bash
pip install -r backend/requirements.txt
```

## Running

Start the server from the `backend` directory:

```bash
cd backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Open your browser to `http://127.0.0.1:8000`
