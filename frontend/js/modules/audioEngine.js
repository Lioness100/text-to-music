let audioContext = null;
let player = null;
let instruments = [];
let instrumentsLoaded = false;
let masterGainNode = null;
let pianoGainNode = null;
let scheduledEvents = [];

async function init() {
  if (!audioContext) {
    audioContext = new AudioContext();
    player = new WebAudioFontPlayer();

    masterGainNode = audioContext.createGain();
    masterGainNode.gain.value = 0.2;
    masterGainNode.connect(audioContext.destination);

    pianoGainNode = audioContext.createGain();
    pianoGainNode.gain.value = 2;
    pianoGainNode.connect(masterGainNode);

    if (!instrumentsLoaded) {
      await loadInstruments();
    }
  }
}

async function loadInstruments() {
  const statusSpan = document.getElementById("playback-status");
  statusSpan.textContent = "Loading instruments...";

  const instrumentNames = ["0000_SBLive_sf2", "0330_FluidR3_GM_sf2_file", "0480_FluidR3_GM_sf2_file", "0890_Chaos_sf2_file"];

  await Promise.all(
    instrumentNames.map((name) => {
      const script = document.createElement("script");
      script.src = `https://surikov.github.io/webaudiofontdata/sound/${name}.js`;
      document.head.appendChild(script);
      return new Promise((resolve) => (script.onload = resolve));
    }),
  );

  instruments = instrumentNames.map((name) => {
    player.loader.decodeAfterLoading(audioContext, `_tone_${name}`);
    return window[`_tone_${name}`];
  });

  instrumentsLoaded = true;
  statusSpan.textContent = "Instruments loaded and decoded!";
}

export async function playMidi(midiUrl, onNoteHighlight) {
  await init();

  if (audioContext.state === "suspended") {
    await audioContext.resume();
  }

  const response = await fetch(midiUrl);
  if (!response.ok) {
    throw new Error(`Failed to fetch MIDI file: ${response.status}`);
  }

  const midiData = new Midi(await response.arrayBuffer());
  const startTime = audioContext.currentTime;
  let melodyNoteIndex = 0;
  scheduledEvents = [];

  midiData.tracks.forEach((track, trackIndex) => {
    if (!instruments[trackIndex]) return;

    track.notes.forEach((note) => {
      const envelope = player.queueWaveTable(
        audioContext,
        trackIndex === 0 ? pianoGainNode : masterGainNode,
        instruments[trackIndex],
        startTime + note.time,
        note.midi,
        note.duration,
        note.velocity,
      );

      if (envelope) {
        scheduledEvents.push({ type: "envelope", envelope });
      }

      if (trackIndex === 0 && onNoteHighlight) {
        const idx = melodyNoteIndex++;
        scheduledEvents.push(
          setTimeout(() => onNoteHighlight(idx), note.time * 1000),
        );
      }
    });
  });

  return midiData.duration;
}

export function stopPlayback() {
  scheduledEvents.forEach((event) => {
    if (event?.type === "envelope") {
      event.envelope?.cancel?.();
    } else {
      clearTimeout(event);
    }
  });
  scheduledEvents = [];

  if (audioContext && player) {
    player.cancelQueue(audioContext);
  }
}
