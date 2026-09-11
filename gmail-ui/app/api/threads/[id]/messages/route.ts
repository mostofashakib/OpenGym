import { NextResponse, type NextRequest } from "next/server"
import { replyToThread } from "@/lib/store"

// POST /api/threads/:id/messages
// Body: { body: string; html?: string; to?: string[]; cc?: string[]; bcc?: string[] }
export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const payload = (await request.json()) as { body?: string; html?: string; to?: string[]; cc?: string[]; bcc?: string[]; replyToId?: string }
    const { id } = await params
    const result = replyToThread(id, { body: payload.body ?? "", html: payload.html, to: payload.to, cc: payload.cc, bcc: payload.bcc, replyToId: payload.replyToId })
    if (!result) return NextResponse.json({ error: "Not found" }, { status: 404 })
    return NextResponse.json(result, { status: 201 })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}
export const dynamic = "force-dynamic"
