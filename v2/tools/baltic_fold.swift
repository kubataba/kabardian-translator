// Generates kabardian_translator/data/baltic-fold.json: the SayFable app's answer (PiperTextPrep.fold, its table,
// diacritics and ICU transliteration) for every letter outside the lv/lt/et alphabets, so Python needs no ICU.
//   swiftc -O -o /tmp/foldmap tools/baltic_fold.swift && /tmp/foldmap kabardian_translator/data/baltic-fold.json
// Keep the copied functions identical to Services/Audio/Piper/PiperTextPrep.swift in SayFableUltra.
import Foundation

// Verbatim copy of PiperTextPrep.fold/table and the three alphabets (SayFableUltra), dumping the answer per letter.
let alphabets: [String: Set<Character>] = [
  "lv": Set("aābcčdeēfgģhiījkķlļmnņoprsštuūvzž"),
  "lt": Set("aąbcčdeęėfghiįyjklmnoprsštuųūvzž"),
  "et": Set("abcdefghijklmnopqrsšzžtuvwõäöüxy")]
func table(for language: String) -> [Character: String] {
    var t: [Character: String] = ["w": "v", "q": "k", "x": "ks", "y": "i", "ß": "ss", "ø": "o", "č": "tš"]
    if language == "et" { t["ø"] = "ö" }
    return t
}
func fold(_ ch: Character, alphabet: Set<Character>, table: [Character: String]) -> String? {
    if let r = table[ch] { return r }
    let scalars = Array(String(ch).decomposedStringWithCanonicalMapping.unicodeScalars)
    if scalars.count > 1 {
        for k in stride(from: scalars.count - 1, through: 1, by: -1) {
            var s = ""
            s.unicodeScalars.append(contentsOf: scalars.prefix(k))
            let c = Character(s.precomposedStringWithCanonicalMapping)
            if alphabet.contains(c) { return String(c) }
            if let r = table[c] { return r }
        }
    }
    for transform in ["Any-Latin", "Any-Latin; Latin-ASCII"] {
        guard let latin = String(ch).applyingTransform(StringTransform(transform), reverse: false)?
            .lowercased(), !latin.isEmpty else { continue }
        var out = ""
        var ok = true
        for c in latin where c.isLetter {
            if alphabet.contains(c) { out.append(c) }
            else if let r = table[c] { out += r }
            else { ok = false; break }
        }
        if ok, !out.isEmpty { return out }
    }
    return nil
}
let ranges: [ClosedRange<UInt32>] = [0x00C0...0x024F, 0x0250...0x02AF, 0x0370...0x03FF, 0x0400...0x052F,
                                     0x0530...0x058F, 0x10A0...0x10FF, 0x1E00...0x1FFF, 0xFB00...0xFB06]
var out: [String: [String: String]] = [:]
for (lang, alpha) in alphabets {
    let t = table(for: lang)
    var m: [String: String] = [:]
    for r in ranges { for v in r {
        guard let u = Unicode.Scalar(v) else { continue }
        let ch = Character(u)
        guard ch.isLetter else { continue }
        let lower = Character(ch.lowercased())
        if alpha.contains(ch) || alpha.contains(lower) { continue }
        m[String(u)] = fold(lower, alphabet: alpha, table: t) ?? ""
    } }
    // the ASCII letters outside the alphabet go through the table too (w q x y for lv/lt)
    for v in UInt32(0x61)...UInt32(0x7A) {
        let ch = Character(Unicode.Scalar(v)!)
        if !alpha.contains(ch) { m[String(ch)] = fold(ch, alphabet: alpha, table: t) ?? "" }
    }
    out[lang] = m
}
let data = try! JSONSerialization.data(withJSONObject: out, options: [.sortedKeys])
FileManager.default.createFile(atPath: CommandLine.arguments[1], contents: data)
print(out.mapValues { $0.count })
