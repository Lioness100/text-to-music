const VF = Vex.Flow;

function midiToNoteName(midi) {
  const noteNames = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"];
  const octave = Math.floor(midi / 12) - 1;
  const noteIndex = midi % 12;
  return `${noteNames[noteIndex]}/${octave}`;
}

function durationToVexFlow(duration) {
  if (duration >= 1.5) return "h";
  if (duration >= 0.75) return "q";
  if (duration >= 0.375) return "8";
  return "16";
}

export function renderSheetMusic(outputDiv, notes, phonemes) {
  outputDiv.innerHTML = "";

  const containerWidth = outputDiv.clientWidth || 800;
  const staveWidth = Math.max(500, containerWidth - 40);
  const staveHeight = 120;
  const notesPerLine = 16;
  const startX = 10;
  const startY = 40;

  const vfNotes = notes.slice(0, 50).map((note, i) => {
    const phoneme = phonemes[i - 4] || "";
    const isSpace = note.pitch === 24 && note.velocity <= 2;
    const duration = durationToVexFlow(note.duration);

    if (isSpace) {
      return new VF.StaveNote({ keys: ["b/4"], duration: duration + "r", clef: "treble" });
    }

    const staveNote = new VF.StaveNote({
      keys: [midiToNoteName(note.pitch)],
      duration,
      clef: "treble",
    });

    if (phoneme && phoneme !== " ") {
      staveNote.addModifier(
        new VF.Annotation(phoneme).setVerticalJustification(
          VF.Annotation.VerticalJustify.BOTTOM,
        ),
      );
    }

    return staveNote;
  });

  if (!vfNotes.length) return;

  const lines = [];
  for (let i = 0; i < vfNotes.length; i += notesPerLine) {
    lines.push(vfNotes.slice(i, i + notesPerLine));
  }

  const totalHeight = startY + lines.length * staveHeight + 50;
  const renderer = new VF.Renderer(outputDiv, VF.Renderer.Backends.SVG);
  renderer.resize(staveWidth + 20, totalHeight);
  const context = renderer.getContext();

  lines.forEach((lineNotes, lineIndex) => {
    const y = startY + lineIndex * staveHeight;
    const stave = new VF.Stave(startX, y, staveWidth);

    if (lineIndex === 0) {
      stave.addTimeSignature("4/4");
    }

    stave.addClef("treble").setContext(context).draw();

    const lineBeats = lineNotes.reduce((sum, note) => {
      const dur = note.duration?.toString().replace("r", "") || "q";
      return sum + ({ h: 2, q: 1, 8: 0.5, 16: 0.25 }[dur] || 1);
    }, 0);

    const voice = new VF.Voice({
      num_beats: Math.ceil(lineBeats),
      beat_value: 4,
    }).setMode(VF.Voice.Mode.SOFT);

    voice.addTickables(lineNotes);
    new VF.Formatter()
      .joinVoices([voice])
      .formatToStave([voice], stave, { align_rests: false });
    voice.draw(context, stave);
  });
}

export function highlightNote(index) {
  document.querySelectorAll(".vf-stavenote").forEach((note, i) => {
    note.style.fill = i === index ? "#667eea" : "";
  });
}
