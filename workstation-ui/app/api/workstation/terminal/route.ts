import { NextRequest, NextResponse } from "next/server"
import { runTerminalCommand } from "@/lib/workstation-client"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { command } = body
    const res = await runTerminalCommand(command || "ls -la")
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
