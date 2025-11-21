import * as audioEngine from "./modules/audioEngine.js";
import * as sheetMusic from "./modules/sheetMusic.js";
import * as api from "./modules/api.js";
import * as phonemeVisualizer from "./modules/phonemeVisualizer.js";

let currentMidiFile = null;
let isPlaying = false;

window.switchTab = function (tab) {
  document
    .querySelectorAll(".tab")
    .forEach((t) => t.classList.remove("active"));
  document
    .querySelectorAll(".tab-content")
    .forEach((c) => c.classList.remove("active"));

  event.target.classList.add("active");
  document.getElementById(`${tab}-tab`).classList.add("active");

  if (tab === "theory" && !document.getElementById("phoneme-staff").innerHTML) {
    phonemeVisualizer.renderPhonemeStaff(
      document.getElementById("phoneme-staff"),
    );
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("drop-zone");
  const midiInput = document.getElementById("midi-input");

  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  dropZone.addEventListener("dragenter", () => dropZone.classList.add("drag-over"));
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("dragover", () => dropZone.classList.add("drag-over"));

  dropZone.addEventListener("drop", (e) => {
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  });

  dropZone.addEventListener("click", () => midiInput.click());
  midiInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  function handleFileSelection(file) {
    if (!file.name.endsWith(".mid") && !file.name.endsWith(".midi")) {
      alert("Please select a MIDI file (.mid or .midi)");
      return;
    }

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    midiInput.files = dataTransfer.files;

    dropZone.querySelector(".drop-zone-text").textContent = file.name;
    window.decodeMusic();
  }
});

window.encodeText = async function () {
  const text = document.getElementById("text-input").value.trim();

  if (!text) {
    alert("Please enter text to encode");
    return;
  }

  const loading = document.getElementById("encode-loading");
  const downloadLink = document.getElementById("download-link");
  const playBtn = document.getElementById("play-btn");

  loading.classList.add("active");
  downloadLink.style.display = "none";

  try {
    const data = await api.encodeText(text);

    currentMidiFile = data.midi_file;

    downloadLink.href = `/download/${data.midi_file}`;
    downloadLink.download = data.midi_file.split("/").pop();
    downloadLink.style.display = "inline-block";

    playBtn.disabled = false;

    sheetMusic.renderSheetMusic(
      document.getElementById("vexflow-output"),
      data.notes,
      data.phonemes,
    );
  } catch (error) {
    alert(`Encoding failed: ${error.message}`);
  } finally {
    loading.classList.remove("active");
  }
};

function stopPlayback() {
  const playBtn = document.getElementById("play-btn");
  const statusSpan = document.getElementById("playback-status");

  audioEngine.stopPlayback();
  sheetMusic.highlightNote(-1);
  playBtn.textContent = "Play";
  statusSpan.textContent = "Ready to play";
  isPlaying = false;
}

window.togglePlayback = async function () {
  const playBtn = document.getElementById("play-btn");
  const statusSpan = document.getElementById("playback-status");

  if (!currentMidiFile) {
    return;
  }

  if (isPlaying) {
    stopPlayback();
  } else {
    playBtn.textContent = "Pause";
    statusSpan.textContent = "Playing...";
    isPlaying = true;

    try {
      const midiUrl = `/download/${currentMidiFile}`;
      const duration = await audioEngine.playMidi(midiUrl, (index) => {
        if (isPlaying) {
          sheetMusic.highlightNote(index);
        }
      });

      setTimeout(() => {
          if (isPlaying) {
            stopPlayback();
          }
        },
duration * 1000 + 500,
      );
    } catch (error) {
      console.error("MIDI playback error:", error);
      alert("Failed to play MIDI file: " + error.message);
      stopPlayback();
    }
  }
};

window.decodeMusic = async function () {
  const file = document.getElementById("midi-input").files[0];
  if (!file) {
    alert("Please select a MIDI file");
    return;
  }

  const loading = document.getElementById("decode-loading");
  const result = document.getElementById("decode-result");

  loading.classList.add("active");
  result.style.display = "none";

  try {
    const decodeData = await api.decodeMusic(file);
    const encodeData = await api.encodeText(decodeData.decoded_text);
    
    displayDecodeResults({
      decoded_text: decodeData.decoded_text,
      notes: encodeData.notes,
      phonemes: encodeData.phonemes,
    });
  } catch (error) {
    alert(`Decoding failed: ${error.message}`);
  } finally {
    loading.classList.remove("active");
  }
};

function displayDecodeResults(data) {
  const resultDiv = document.getElementById("decode-result");
  const textDiv = document.getElementById("decoded-text");
  const sheetContainer = document.getElementById("decode-sheet-container");
  const placeholder = document.getElementById("decode-placeholder");

  textDiv.innerHTML = `<p style="font-size: 1.2em; line-height: 1.8;">${data.decoded_text}</p>`;
  resultDiv.style.display = "block";
  
  // Display sheet music from re-encoded text
  if (data.notes && data.phonemes) {
    placeholder.style.display = "none";
    sheetContainer.style.display = "block";
    sheetMusic.renderSheetMusic(
      document.getElementById("decode-vexflow-output"),
      data.notes,
      data.phonemes,
    );
  }
}
