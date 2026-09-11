import { NextResponse, type NextRequest } from "next/server"
import { listLabels, setLabels } from "@/lib/store"

// GET /api/labels
export async function GET() {
  return NextResponse.json({ labels: listLabels() })
}

// PUT /api/labels
// Body: { labels: Array<{ id: string; name: string; type: 'SYSTEM' | 'USER'; color?: string }> }
export async function PUT(request: NextRequest) {
  try {
    const payload = (await request.json()) as {
      labels?: Array<{ id: string; name: string; type: "SYSTEM" | "USER"; color?: string }>
    }
    if (!Array.isArray(payload.labels)) {
      return NextResponse.json({ error: "labels must be an array" }, { status: 400 })
    }
    const labels = setLabels(payload.labels)
    return NextResponse.json({ labels })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

// POST /api/labels
// Body: { name: string; id?: string; color?: string }
export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { name?: string; id?: string; color?: string }
    const rawName = typeof body?.name === "string" ? body.name.trim() : ""
    if (!rawName) {
      return NextResponse.json({ error: "name is required" }, { status: 400 })
    }
    const existing = listLabels()
    const systemIds = new Set(existing.filter((l) => l.type === "SYSTEM").map((l) => l.id))
    const allIds = new Set(existing.map((l) => l.id))

    const slugify = (s: string) =>
      s
        .toLowerCase()
        .replace(/[^a-z0-9]+/gi, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 50) || "label"

    const baseId = (typeof body?.id === "string" && body.id.trim().length > 0 ? body.id.trim() : slugify(rawName))
    let candidate = baseId
    let suffix = 2
    while (allIds.has(candidate) || systemIds.has(candidate.toUpperCase())) {
      candidate = `${baseId}-${suffix}`
      suffix += 1
    }

    const newLabel = { id: candidate, name: rawName, type: "USER" as const, color: typeof body?.color === "string" ? body.color : undefined }
    const updated = setLabels([...existing, newLabel])
    const created = updated.find((l) => l.id === candidate) || newLabel
    return NextResponse.json({ label: created, labels: updated }, { status: 201 })
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

export const dynamic = "force-dynamic"
