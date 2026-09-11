import { NextResponse } from "next/server"
import { getState } from "@/lib/store"

type Contact = { email: string; name?: string; count: number }

function extractEmailAddress(value: string | undefined): string {
  if (typeof value !== "string" || value.length === 0) return ""
  const match = value.match(/<([^>]+)>/)
  const addr = (match ? match[1] : value).trim().toLowerCase()
  return addr
}

function extractDisplayName(value: string | undefined): string | undefined {
  if (typeof value !== "string" || value.length === 0) return undefined
  const nameMatch = value.match(/^([^<]+)</)
  const name = nameMatch ? nameMatch[1].trim() : undefined
  if (name && name.length > 0) return name
  return undefined
}

export async function GET() {
  const state = getState()
  const me = String(state?.settings?.email || "you@example.com").toLowerCase()
  const contacts = new Map<string, Contact>()

  const add = (raw: string | undefined, weight = 1) => {
    const email = extractEmailAddress(raw)
    if (!email || !email.includes("@")) return
    const name = extractDisplayName(raw)
    const prev = contacts.get(email)
    if (prev) {
      prev.count += weight
      if (!prev.name && name) prev.name = name
    } else {
      contacts.set(email, { email, name, count: weight })
    }
  }

  for (const m of state.messages) {
    // weigh sender a bit higher; include recipients
    add(m.from, 2)
    for (const t of m.to || []) add(t, 1)
    for (const c of m.cc || []) add(c, 1)
    for (const b of m.bcc || []) add(b, 1)
  }

  // Merge in directory contacts if present on state (supports contacts or legacy users)
  try {
    const directory: Record<string, { email?: string; name?: string }> = (state as any)?.contacts ?? (state as any)?.users ?? {}
    if (directory && typeof directory === "object") {
      for (const value of Object.values(directory)) {
        const email = typeof value?.email === "string" ? value.email : ""
        const name = typeof value?.name === "string" ? value.name : undefined
        if (!email || !email.includes("@")) continue
        add(name ? `${name} <${email}>` : email, 3)
      }
    }
  } catch {}

  // Ensure my own email is present in suggestions
  if (me) {
    const displayName = (state?.settings?.displayName || "").trim() || undefined
    const existing = contacts.get(me)
    if (existing) {
      if (!existing.name && displayName) existing.name = displayName
      // bump a little so it doesn't sink below random low-frequency contacts
      existing.count += 1
    } else {
      contacts.set(me, { email: me, name: displayName, count: 1 })
    }
  }

  // Convert to list and sort by frequency (descending)
  const list = Array.from(contacts.values()).sort((a, b) => b.count - a.count)

  return NextResponse.json({ contacts: list })
}

export const dynamic = "force-dynamic"
export const runtime = "nodejs"


