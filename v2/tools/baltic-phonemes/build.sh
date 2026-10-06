#!/bin/sh
# Builds baltic-phonemes from the SayFable app sources (SAYFABLE repo path as $1) into the package's bin folder.
set -e
REPO="${1:-$HOME/Desktop/SayFableUltra}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/../../kabardian_translator/bin"
mkdir -p "$OUT"
P="$REPO/Services/Audio/Piper"
swiftc -O -D SAYFABLE_CLI -target arm64-apple-macos13 -o "$OUT/baltic-phonemes" \
  "$HERE/main.swift" "$HERE/shims.swift" \
  "$P/BalticPhonemes.swift" "$P/PiperTextPrep.swift" "$P/LatvianPhonemizer.swift" "$P/LithuanianPhonemizer.swift" \
  "$P/EstonianPhonemizer.swift" "$P/NumeralSpeller.swift" "$P/RomanNumeral.swift" "$P/PhonemizerReport.swift" \
  "$REPO/Services/Semantic/MorphResource.swift" "$REPO/Services/Semantic/ReloadableTable.swift" \
  "$REPO/Services/Log.swift" \
  "$REPO/Services/Semantic/FinnoUgricAnalyzer.swift" "$REPO/Services/Semantic/LatvianAnalyzer.swift" \
  "$REPO/Services/Semantic/LithuanianAnalyzer.swift"
echo "built $OUT/baltic-phonemes"
