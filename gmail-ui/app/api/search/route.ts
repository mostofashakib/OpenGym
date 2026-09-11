import { NextResponse, type NextRequest } from "next/server"
import { listEmails } from "@/lib/store"

// GET /api/search?q=...&folder=...&label=...&starred=...&unread=...
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get("q") || undefined
  const folder = (searchParams.get("folder") as any) || undefined
  const label = searchParams.get("label") || undefined
  const starred = searchParams.get("starred")
  const unread = searchParams.get("unread")

  const messages = listEmails({
    q,
    folder,
    label,
    starred: starred === null ? undefined : starred === "true",
    unread: unread === null ? undefined : unread === "true",
  })
  return NextResponse.json({ messages })
}

export const dynamic = "force-dynamic"
