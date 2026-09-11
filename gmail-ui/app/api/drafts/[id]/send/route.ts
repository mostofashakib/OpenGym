import { NextResponse, type NextRequest } from "next/server"
import { getEmailById, sendDraft, updateEmail } from "@/lib/store"

// POST /api/drafts/:id/send
// Body: { to: string[]; cc?: string[]; bcc?: string[]; subject: string; text: string; html?: string }
export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const draft = getEmailById(id)
    if (!draft || !Array.isArray(draft.labelIds) || !draft.labelIds.includes("DRAFTS")) {
      return NextResponse.json({ error: "Not found" }, { status: 404 })
    }
    const payload = (await request.json()) as {
      to?: string[]
      cc?: string[]
      bcc?: string[]
      subject?: string
      text?: string
      html?: string
    }
    // Ensure we preserve any fields not provided by the client
    const to = Array.isArray(payload.to) ? payload.to : draft.to
    const cc = Array.isArray(payload.cc) ? payload.cc : draft.cc
    const bcc = Array.isArray(payload.bcc) ? payload.bcc : draft.bcc
    const subject = typeof payload.subject === "string" ? payload.subject : draft.subject
    const text = typeof payload.text === "string" ? payload.text : draft.text || ""
    const html = typeof payload.html === "string" ? payload.html : draft.html
    const result = sendDraft(id, { to, cc, bcc, subject, text, html })
    if (!result) return NextResponse.json({ error: "Unable to send" }, { status: 400 })
    return NextResponse.json(result, { status: 201 })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

export const dynamic = "force-dynamic"
