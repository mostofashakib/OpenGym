import { NextResponse, type NextRequest } from "next/server"
import { listEmails, getEmailById, moveThreadToSystemFolder } from "@/lib/store"

// GET /api/folders/:name/messages
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const { name } = await params
  const folder = name as "inbox" | "sent" | "drafts" | "trash" | "archive" | "spam" | "all"
  const messages = listEmails({ folder })
  return NextResponse.json({ messages })
}

// PUT /api/folders/:name/messages
// Body: { messageIds: string[] } -> move provided messages into this folder
export async function PUT(request: NextRequest, { params }: { params: Promise<{ name: string }> }) {
  try {
    const payload = (await request.json()) as { messageIds?: string[] }
    if (!Array.isArray(payload.messageIds)) {
      return NextResponse.json({ error: "messageIds must be an array" }, { status: 400 })
    }
    const { name } = await params
    const folder = name as "inbox" | "sent" | "drafts" | "trash" | "archive" | "spam"
    // Move entire threads for provided messages
    const threadIds = Array.from(
      new Set(
        payload.messageIds
          .map((id) => getEmailById(id))
          .filter((m): m is NonNullable<ReturnType<typeof getEmailById>> => Boolean(m))
          .map((m) => m.threadId || m.id),
      ),
    )
    for (const tid of threadIds) moveThreadToSystemFolder(tid, folder)
    return NextResponse.json({ updated: threadIds.length })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

export const dynamic = "force-dynamic"
export const runtime = "nodejs"
