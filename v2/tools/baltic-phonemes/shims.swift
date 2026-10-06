// App-only types referenced by the shared sources, reduced to what a command-line phonemizer needs.
import Foundation
enum MemoryProbe { static func appendLine(_ line: String) {} }
// POSCode is declared in the app's TokenIndex.swift; the analyzers need only the enum.
enum POSCode: UInt8, Codable, Sendable {
    case other = 0, noun, verb, adj, adv, pron, propn, num, punct, det, adp, cconj, sconj
}
// PhonemizerReport prints the English G2P cost; English is not phonemized here.
enum EnglishG2P { static func takeStats() -> (runs: Int, ms: Double) { (0, 0) } }
