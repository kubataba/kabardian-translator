// baltic-phonemes — the SayFable app's own Latvian, Lithuanian and Estonian text layer and phonemizers, compiled
// from the app's sources (build.sh), so the Baltic Piper model gets exactly the input it was trained on.
//
// stdin, one line per item:   <lang>\t<text>        lang ∈ lv, lt, et
// stdout, one line per item:  <phoneme string>      (the model's notation; ids are mapped by the caller)
// Dictionaries lt.dict / et.dict are read from the folder of this executable (MorphResource, "next to the CLI").
import Foundation

setvbuf(stdout, nil, _IOLBF, 0)
while let line = readLine(strippingNewline: true) {
    let parts = line.split(separator: "\t", maxSplits: 1, omittingEmptySubsequences: false)
    guard parts.count == 2 else { print(""); continue }
    let lang = String(parts[0])
    let text = String(parts[1]).replacingOccurrences(of: "\u{2028}", with: " ")
    let prepared = PiperTextPrep.prepare(text, language: lang, count: false)
    print(BalticPhonemes.phonemeString(prepared, language: lang) ?? "")
}
