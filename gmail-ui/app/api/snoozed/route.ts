import { type NextRequest, NextResponse } from "next/server"
import { listSnoozed, snoozeEmail, getThread } from "@/lib/store"

// GET /api/snoozed
export async function GET() {
  const messages = listSnoozed()
  const threadIsStarredById: Record<string, boolean> = {}
  for (const m of messages) {
    const tid = (m?.threadId || m?.id) as string
    if (tid && threadIsStarredById[tid] === undefined) {
      const t = getThread(tid)
      threadIsStarredById[tid] = Boolean(t?.isStarred)
    }
  }
  return NextResponse.json({ messages, threadIsStarredById })
}

// POST /api/snoozed
// Body can be either:
// - { id: string, snoozeUntil: string } to snooze a single message
// or legacy: { messages: EmailMessage[] } to replace snoozed messages entirely (kept for compatibility)
export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as any
    if (typeof payload?.id === "string") {
      const updated = snoozeEmail(payload.id, payload.snoozeUntil ?? null)
      if (!updated) return NextResponse.json({ error: "Not found" }, { status: 404 })
      return NextResponse.json({ message: updated })
    }
    if (Array.isArray(payload?.messages)) {
      // Best-effort legacy support: apply snooze on provided items
      const results = payload.messages.map((m: any) => snoozeEmail(m.id, m.snoozeUntil ?? null))
      return NextResponse.json({ updated: results })
    }
    return NextResponse.json({ error: "Invalid payload" }, { status: 400 })
  } catch (error) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

// PUT /api/snoozed
// Body: { id: string, snoozeUntil?: string | null }
export async function PUT(request: NextRequest) {
  try {
    const payload = (await request.json()) as { id?: string; snoozeUntil?: string | null }
    if (typeof payload.id !== "string") {
      return NextResponse.json({ error: "id is required" }, { status: 400 })
    }
    const updated = snoozeEmail(payload.id, payload.snoozeUntil ?? null)
    if (!updated) return NextResponse.json({ error: "Not found" }, { status: 404 })
    return NextResponse.json({ message: updated })
  } catch (error) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}
export const dynamic = "force-dynamic"
