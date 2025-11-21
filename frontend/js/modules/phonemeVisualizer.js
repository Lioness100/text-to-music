const VF = Vex.Flow;

const phonemeMappings = [
  { category: 'Voiceless stops', phonemes: [{p:'p',n:'c/4'},{p:'t',n:'d/4'},{p:'k',n:'e/4'}] },
  { category: 'Voiced stops', phonemes: [{p:'b',n:'c/3'},{p:'d',n:'d/3'},{p:'ɡ',n:'e/3'}] },
  { category: 'Fricatives', phonemes: [{p:'v',n:'f/4'},{p:'f',n:'g/4'},{p:'z',n:'g/4'},{p:'ð',n:'a#/4'},{p:'s',n:'a/4'},{p:'ʒ',n:'a/4'},{p:'ʃ',n:'b/4'},{p:'θ',n:'c/5'},{p:'h',n:'d/5'}] },
  { category: 'Nasals', phonemes: [{p:'m',n:'g/3'},{p:'n',n:'a/3'},{p:'ŋ',n:'b/3'}] },
  { category: 'Liquids', phonemes: [{p:'ɫ',n:'c/4'},{p:'l',n:'d/4'},{p:'ɹ',n:'e/4'}] },
  { category: 'Approximants', phonemes: [{p:'w',n:'f/3'},{p:'j',n:'f/5'}] },
  { category: 'Affricates', phonemes: [{p:'dʒ',n:'d/5'},{p:'tʃ',n:'e/5'}] },
  { category: 'High vowels', phonemes: [{p:'ɪ',n:'f/5'},{p:'i',n:'g/5'},{p:'ʊ',n:'g/5'},{p:'u',n:'a/5'}] },
  { category: 'Mid vowels', phonemes: [{p:'ɝ',n:'g/4'},{p:'ə',n:'a/4'},{p:'ɔ',n:'a/4'},{p:'o',n:'b/4'},{p:'ɛ',n:'c/5'},{p:'e',n:'d/5'}] },
  { category: 'Low vowels', phonemes: [{p:'ɑ',n:'d/4'},{p:'a',n:'e/4'},{p:'æ',n:'f/4'}] },
  { category: 'Diphthongs', phonemes: [{p:'aʊ',n:'d/4'},{p:'aɪ',n:'e/4'},{p:'ɔɪ',n:'a/4'},{p:'oʊ',n:'b/4'},{p:'eɪ',n:'d/5'}] }
];

export function renderPhonemeStaff(outputDiv) {
  outputDiv.innerHTML = "";

  const containerWidth = outputDiv.clientWidth || 800;
  const staveWidth = Math.max(700, containerWidth - 100);
  const staveHeight = 140;
  const startX = 10;
  const startY = 20;

  const totalHeight = startY + phonemeMappings.length * staveHeight + 50;
  const renderer = new VF.Renderer(outputDiv, VF.Renderer.Backends.SVG);
  renderer.resize(staveWidth + 20, totalHeight);
  const context = renderer.getContext();

  phonemeMappings.forEach((group, groupIndex) => {
    const y = startY + groupIndex * staveHeight;
    const stave = new VF.Stave(startX, y, staveWidth);
    stave.addClef("treble");
    stave.setText(group.category, VF.Modifier.Position.ABOVE, { shift_x: 0, shift_y: -10 });
    stave.setContext(context).draw();

    const vfNotes = group.phonemes.map((ph) => {
      const note = new VF.StaveNote({ keys: [ph.n], duration: "q", clef: "treble" });
      note.addModifier(
        new VF.Annotation(ph.p)
          .setVerticalJustification(VF.Annotation.VerticalJustify.BOTTOM)
          .setFont("Arial", 12),
      );
      return note;
    });

    const voice = new VF.Voice({
      num_beats: group.phonemes.length,
      beat_value: 4,
    }).setMode(VF.Voice.Mode.SOFT);

    voice.addTickables(vfNotes);
    new VF.Formatter()
      .joinVoices([voice])
      .formatToStave([voice], stave, { align_rests: false });
    voice.draw(context, stave);
  });
}
