import { NextRequest, NextResponse } from "next/server"
import { submitAudit } from "@/lib/browser-client"

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { summary, audited_ids } = body

    if (!summary || typeof summary !== "string") {
      return NextResponse.json({ error: "Missing or invalid 'summary'" }, { status: 400 })
    }

    const res = await submitAudit(summary, audited_ids || [])
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
