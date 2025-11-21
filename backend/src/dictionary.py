import re

from .phoneme_mapping import IPA_TO_MUSIC


def load_cmu_dict(filepath: str) -> dict:
    cmu_dict = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                word, pronunciation = parts
                pronunciations = pronunciation.split(",")
                if word not in cmu_dict:
                    cmu_dict[word] = []
                for pron in pronunciations:
                    cmu_dict[word].append(pron.strip().strip("/"))
    return cmu_dict


def build_reverse_cmu_dict(cmu_dict: dict) -> dict:
    reverse_cmu = {}
    for word, pronunciations in cmu_dict.items():
        for pron in pronunciations:
            clean_pron = pron.replace("ˈ", "").replace("ˌ", "").replace(" ", "")
            if clean_pron not in reverse_cmu:
                reverse_cmu[clean_pron] = word
    return reverse_cmu


def text_to_ipa(text: str, cmu_dict: dict) -> str:
    words = re.findall(r"\b\w+\b", text.lower())
    ipa_sequence = []

    for word in words:
        if word in cmu_dict:
            ipa = cmu_dict[word][0]
            ipa_sequence.append(ipa)
        else:
            ipa_sequence.append(word)

    return " ".join(ipa_sequence)


def ipa_to_phonemes(ipa_string: str) -> list:
    if " " in ipa_string:
        words = ipa_string.split(" ")
        result = []
        for i, word in enumerate(words):
            result.extend(ipa_to_phonemes(word))
            if i < len(words) - 1:
                result.append(" ")
        return result

    result = []
    i = 0
    while i < len(ipa_string):
        if i < len(ipa_string) - 1 and ipa_string[i : i + 2] in IPA_TO_MUSIC:
            result.append(ipa_string[i : i + 2])
            i += 2
        elif ipa_string[i] in IPA_TO_MUSIC:
            result.append(ipa_string[i])
            i += 1
        else:
            i += 1
    return result
