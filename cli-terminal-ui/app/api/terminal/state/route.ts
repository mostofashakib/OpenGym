import { NextResponse } from "next/server"
import { getSystemState, listSystemFiles } from "@/lib/terminal-client"

export async function GET() {
  try {
    const sysState = await getSystemState()
    const files = await listSystemFiles()
    return NextResponse.json({
      ...sysState,
      files,
    })
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Failed to fetch state" }, { status: 500 })
  }
}
