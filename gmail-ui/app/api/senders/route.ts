import { NextResponse, type NextRequest } from "next/server"
import { getState } from "@/lib/store"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = (searchParams.get("q") || "").toLowerCase()

  const state = getState()
  // Key by email where possible to avoid duplicates; fall back to name when no email
  const byKey = new Map<string, { name: string; email: string; count: number }>()

  for (const m of state.messages) {
    if (!m?.from) continue
    const from = String(m.from)
    const nameMatch = from.match(/^([^<]+)</)
    const emailMatch = from.match(/<([^>]+)>/)
    const bareEmail = !emailMatch && from.includes("@") ? from.trim() : ""
    const rawName = nameMatch ? nameMatch[1].trim() : (bareEmail || from)
    const email = (emailMatch ? emailMatch[1] : bareEmail).trim()
    // Prefer directory contact name if available
    const contactName = email ? String(state?.contacts?.[email]?.name || "").trim() : ""
    const name = contactName || rawName
    const key = (email || name).toLowerCase()
    if (!byKey.has(key)) byKey.set(key, { name, email, count: 0 })
    byKey.get(key)!.count += 1
  }

  // Merge directory contacts (address book) so entries with known names appear even if
  // messages lacked a friendly From header.
  try {
    const directory = state?.contacts || {}
    for (const [email, info] of Object.entries(directory)) {
      const normalizedEmail = String(email || "").trim()
      if (!normalizedEmail || !normalizedEmail.includes("@")) continue
      const name = String((info as any)?.name || "").trim()
      const key = normalizedEmail.toLowerCase()
      const existing = byKey.get(key)
      if (existing) {
        // Upgrade name if directory has a better one
        if (!existing.name || existing.name === existing.email) {
          if (name) existing.name = name
        }
        existing.email = existing.email || normalizedEmail
        // Slightly bump so directory contacts surface reasonably
        existing.count += 1
      } else {
        byKey.set(key, { name: name || normalizedEmail, email: normalizedEmail, count: 1 })
      }
    }
  } catch {}

  let senders = Array.from(byKey.values())
  if (q) senders = senders.filter((s) => s.name.toLowerCase().includes(q) || s.email.toLowerCase().includes(q))
  senders.sort((a, b) => {
    const al = a.name.toLowerCase()
    const ae = a.email.toLowerCase()
    const bl = b.name.toLowerCase()
    const be = b.email.toLowerCase()
    const aLocal = ae.split("@")[0]
    const bLocal = be.split("@")[0]
    const aScore = (q ? (al.startsWith(q) ? 400 : 0) + (aLocal.startsWith(q) ? 200 : 0) + (al.includes(q) ? 100 : 0) + (ae.includes(q) ? 50 : 0) : 0)
    const bScore = (q ? (bl.startsWith(q) ? 400 : 0) + (bLocal.startsWith(q) ? 200 : 0) + (bl.includes(q) ? 100 : 0) + (be.includes(q) ? 50 : 0) : 0)
    if (aScore !== bScore) return bScore - aScore
    if (a.count !== b.count) return b.count - a.count
    return a.name.localeCompare(b.name)
  })

  return NextResponse.json({ senders: senders.slice(0, 10).map(({ name, email }) => ({ name, email })) })
}

export const dynamic = "force-dynamic"
