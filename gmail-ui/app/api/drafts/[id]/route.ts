import { NextResponse, type NextRequest } from "next/server"
import { getEmailById, updateEmail, softDeleteEmail } from "@/lib/store"

// GET /api/drafts/:id
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const draft = getEmailById(id)
  if (!draft || !draft.labelIds.includes("DRAFTS")) return NextResponse.json({ error: "Not found" }, { status: 404 })
  return NextResponse.json({ draft })
}

// PUT /api/drafts/:id
// Update draft fields (to, cc, bcc, subject, body, attachments)
export async function PUT(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const draft = getEmailById(id)
  if (!draft || !draft.labelIds.includes("DRAFTS")) return NextResponse.json({ error: "Not found" }, { status: 404 })
  try {
    const payload = (await request.json()) as Partial<{
      to: string[]
      cc: string[]
      bcc: string[]
      subject: string
      text: string
      html: string
      attachments: Array<{ id: string; filename: string; mimeType: string; dataBase64: string; size: number }>
    }>
    const updated = updateEmail(id, payload as any)
    return NextResponse.json({ draft: updated })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

// DELETE /api/drafts/:id -> move to trash
export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const draft = getEmailById(id)
  if (!draft || !draft.labelIds.includes("DRAFTS")) return NextResponse.json({ error: "Not found" }, { status: 404 })
  const updated = softDeleteEmail(id)
  return NextResponse.json({ draft: updated })
}

export const dynamic = "force-dynamic"
