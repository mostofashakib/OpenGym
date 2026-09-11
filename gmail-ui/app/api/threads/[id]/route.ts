import { NextResponse, type NextRequest } from "next/server"
import { getThread, updateThread, updateEmail } from "@/lib/store"

// GET /api/threads/:id
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const thread = getThread(id)
  if (!thread) return NextResponse.json({ error: "Not found" }, { status: 404 })
  return NextResponse.json({ thread })
}

// PUT /api/threads/:id
export async function PUT(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const payload = (await request.json()) as { isStarred?: boolean; subject?: string; isRead?: boolean }
    const { id } = await params

    // Handle thread-wide read/unread toggle
    if (typeof payload.isRead === "boolean") {
      const thread = getThread(id)
      if (!thread) return NextResponse.json({ error: "Not found" }, { status: 404 })
      for (const m of thread.messages) updateEmail(m.id, { isRead: payload.isRead })
      const refreshed = getThread(id)
      return NextResponse.json({ thread: refreshed })
    }

    const updated = updateThread(id, { isStarred: payload.isStarred, subject: payload.subject })
    if (updated) return NextResponse.json({ thread: updated })

    // Fallback: if there is no persisted thread record, operate on synthesized thread messages
    const synth = getThread(id)
    if (!synth) return NextResponse.json({ error: "Not found" }, { status: 404 })
    if (typeof payload.isStarred === "boolean") {
      if (payload.isStarred) {
        const last = synth.messages[synth.messages.length - 1]
        if (last) updateEmail(last.id, { isStarred: true })
      } else {
        for (const m of synth.messages) updateEmail(m.id, { isStarred: false })
      }
    }
    const refreshed = getThread(id)
    return NextResponse.json({ thread: refreshed })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

export const dynamic = "force-dynamic"
