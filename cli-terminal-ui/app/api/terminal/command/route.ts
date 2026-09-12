import { NextRequest, NextResponse } from "next/server"
import { executeTerminalCommand } from "@/lib/terminal-client"

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { command, cwd } = body
    if (!command || typeof command !== "string") {
      return NextResponse.json({ error: "Missing or invalid 'command'" }, { status: 400 })
    }

    const result = await executeTerminalCommand(command, cwd || "/home/admin")
    return NextResponse.json(result)
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Failed to execute command" }, { status: 500 })
  }
}
