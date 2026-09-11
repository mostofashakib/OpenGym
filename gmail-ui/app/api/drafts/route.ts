import { NextResponse, type NextRequest } from "next/server"
import { createDraft, listEmails } from "@/lib/store"

// GET /api/drafts
export async function GET() {
  const messages = listEmails({ folder: "drafts" })
  return NextResponse.json({ drafts: messages })
}

// POST /api/drafts
// Body: optional fields to initialize a draft
export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as Partial<{
      to: string[]
      cc: string[]
      bcc: string[]
      subject: string
      text: string
      html: string
      attachments: Array<{ id: string; filename: string; mimeType: string; dataBase64: string; size: number }>
      parentThreadId: string
    }>
    const draft = createDraft(payload as any)
    return NextResponse.json({ draft }, { status: 201 })
  } catch (err) {
    const draft = createDraft()
    return NextResponse.json({ draft }, { status: 201 })
  }
}

export const dynamic = "force-dynamic"
