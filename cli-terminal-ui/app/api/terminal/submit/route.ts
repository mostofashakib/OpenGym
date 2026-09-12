import { NextRequest, NextResponse } from "next/server"
import { submitResolution } from "@/lib/terminal-client"

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { summary, actions_taken } = body
    if (!summary || typeof summary !== "string") {
      return NextResponse.json({ error: "Missing or invalid 'summary'" }, { status: 400 })
    }

    const result = await submitResolution(summary, actions_taken || [])
    return NextResponse.json(result)
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Failed to submit remediation" }, { status: 500 })
  }
}
