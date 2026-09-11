import { NextResponse, type NextRequest } from "next/server"
import { getSettings, updateSettings } from "@/lib/store"

// GET /api/settings
export async function GET() {
  return NextResponse.json({ settings: getSettings() })
}

// PUT /api/settings
// Body: { displayName?: string; signature?: string; email?: string }
export async function PUT(request: NextRequest) {
  try {
    const payload = (await request.json()) as { displayName?: string; signature?: string; email?: string }
    const updated = updateSettings(payload)
    return NextResponse.json({ settings: updated })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

export const dynamic = "force-dynamic"
