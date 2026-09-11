import { NextResponse, type NextRequest } from "next/server"
import {
  getEmailById,
  moveEmailToSystemFolder,
  updateEmail,
  addLabelToEmail,
  removeLabelFromEmail,
  moveThreadToSystemFolder,
  addLabelToThread,
  removeLabelFromThread,
  softDeleteEmail,
  listLabels,
} from "@/lib/store"

// GET /api/emails/:id
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const email = getEmailById(id)
  if (!email || email.isDraftDeleted) return NextResponse.json({ error: "Not found" }, { status: 404 })
  return NextResponse.json({ message: email })
}

// PUT /api/emails/:id
// Accepts partial updates to flags and metadata. Special operations supported via "action":
// - action: "archive" | "trash" | "restore"
// - addLabel: string
// - removeLabel: string
export async function PUT(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const email = getEmailById(id)
  if (!email) return NextResponse.json({ error: "Not found" }, { status: 404 })

  try {
    const payload = (await request.json()) as {
      isRead?: boolean
      isStarred?: boolean
      isImportant?: boolean
      labelIds?: string[]
      subject?: string
      text?: string
      html?: string
      snoozeUntil?: string | null
      action?: "archive" | "trash" | "restore"
      addLabel?: string
      removeLabel?: string
    }

    if (payload.action === "archive") {
      // Apply archive across the whole thread: remove INBOX on all messages in the thread (retain other labels)
      const tid = email.threadId || email.id
      moveThreadToSystemFolder(tid, "archive")
      const refreshed = getEmailById(id)
      return NextResponse.json({ message: refreshed })
    }
    if (payload.action === "trash") {
      // Special-case: drafts are soft-deleted and hidden everywhere
      const isDraft = Array.isArray(email.labelIds) && email.labelIds.includes("DRAFTS")
      if (isDraft) {
        const deleted = softDeleteEmail(id)
        return NextResponse.json({ message: deleted })
      }
      const tid = email.threadId || email.id
      moveThreadToSystemFolder(tid, "trash")
      const refreshed = getEmailById(id)
      return NextResponse.json({ message: refreshed })
    }
    if (payload.action === "restore") {
      const tid = email.threadId || email.id
      moveThreadToSystemFolder(tid, "inbox")
      const refreshed = getEmailById(id)
      return NextResponse.json({ message: refreshed })
    }
    if (typeof payload.addLabel === "string" && payload.addLabel.trim().length > 0) {
      // Propagate USER labels across the entire thread; for SYSTEM labels, apply to the single message
      const lid = payload.addLabel
      const labels = listLabels()
      const ldef = labels.find((l) => l.id === lid)
      const tid = email.threadId || email.id
      if (ldef && ldef.type === "USER") {
        addLabelToThread(tid, lid)
      } else {
        addLabelToEmail(id, lid)
      }
      const refreshed = getEmailById(id)
      return NextResponse.json({ message: refreshed })
    }
    if (typeof payload.removeLabel === "string" && payload.removeLabel.trim().length > 0) {
      const tid = email.threadId || email.id
      removeLabelFromThread(tid, payload.removeLabel)
      const refreshed = getEmailById(id)
      return NextResponse.json({ message: refreshed })
    }

    const updated = updateEmail(id, {
      isRead: payload.isRead,
      isStarred: payload.isStarred,
      isImportant: payload.isImportant,
      labelIds: payload.labelIds,
      subject: payload.subject,
      text: payload.text,
      html: payload.html,
      snoozeUntil: payload.snoozeUntil,
    })
    return NextResponse.json({ message: updated })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

export const dynamic = "force-dynamic"
export const runtime = "nodejs"
