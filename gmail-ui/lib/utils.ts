import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Decode JSON-style escape sequences that may have been preserved in data files.
 *
 * - Converts double-escaped sequences like "\\u2019" to a single-escaped form first
 * - Then converts "\uXXXX" sequences to their Unicode characters for display
 * - Also normalizes common escaped controls like "\\n", "\\r", "\\t"
 */
export function decodeJsonEscapedUnicode(input: string): string {
  if (typeof input !== "string" || input.length === 0) return input
  try {
    // First collapse double-escaped unicode sequences to single-escaped
    let s = input.replace(/\\\\u([0-9a-fA-F]{4})/g, "\\u$1")
    // Replace common double-escaped control sequences
    s = s.replace(/\\n/g, "\n").replace(/\\r/g, "\r").replace(/\\t/g, "\t")
    // Finally, replace single-escaped unicode sequences with actual characters
    s = s.replace(/\\u([0-9a-fA-F]{4})/g, (_m, hex) => String.fromCharCode(parseInt(hex, 16)))
    return s
  } catch {
    return input
  }
}

/**
 * Decode for display: handles JSON escapes (via decodeJsonEscapedUnicode),
 * normalizes stray Windows-1252/Latin-1 smart punctuation and common mojibake
 * sequences, and fixes control-character substitutions sometimes seen in
 * external datasets.
 */
export function decodeForDisplay(input: string): string {
  let s = decodeJsonEscapedUnicode(input)
  if (typeof s !== "string" || s.length === 0) return s
  // Map likely control/CP1252 codes to their intended punctuation
  const cp1252Map: Record<string, string> = {
    "\u0019": "’", // observed corrupted apostrophe
    "\u0091": "‘",
    "\u0092": "’",
    "\u0093": "“",
    "\u0094": "”",
    "\u0095": "•",
    "\u0096": "–",
    "\u0097": "—",
    "\u0098": "˜",
    "\u0099": "™",
  }
  s = s.replace(/[\u0019\u0091-\u0099]/g, (ch) => cp1252Map[ch] ?? ch)
  // Fix common mojibake where UTF-8 was decoded as Latin-1 then re-encoded
  s = s
    .replace(/â€™/g, "’")
    .replace(/â€˜/g, "‘")
    .replace(/â€œ/g, "“")
    .replace(/â€/g, "”")
    .replace(/â€�/g, "”")
    .replace(/â€“/g, "–")
    .replace(/â€”/g, "—")
    .replace(/â€¢/g, "•")
    .replace(/â„¢/g, "™")
  return s
}

/**
 * Convert basic HTML into plain text suitable for previews.
 * - Strips tags, scripts, and styles
 * - Decodes common entities (&nbsp;, &amp;, &lt;, &gt;, &quot;, &#39;)
 * - Collapses whitespace
 */
export function htmlToPlainText(html: string): string {
  if (typeof html !== "string" || html.length === 0) return ""
  try {
    let s = html
    // Remove scripts/styles first
    s = s.replace(/<script[\s\S]*?<\/script>/gi, " ")
    s = s.replace(/<style[\s\S]*?<\/style>/gi, " ")
    // Strip all remaining tags
    s = s.replace(/<[^>]+>/g, " ")
    // Decode a few common entities
    s = s
      .replace(/&nbsp;/gi, " ")
      .replace(/&amp;/gi, "&")
      .replace(/&lt;/gi, "<")
      .replace(/&gt;/gi, ">")
      .replace(/&quot;/gi, '"')
      .replace(/&#39;/gi, "'")
    // Collapse whitespace
    s = s.replace(/\s+/g, " ").trim()
    return s
  } catch {
    return ""
  }
}
