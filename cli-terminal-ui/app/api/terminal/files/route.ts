import { NextRequest, NextResponse } from "next/server"
import { listSystemFiles, runBridge } from "@/lib/terminal-client"

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const filePath = searchParams.get("path")
    if (filePath) {
      const readRes = await runBridge("call_tool", ["read_file", JSON.stringify({ path: filePath })])
      return NextResponse.json(readRes)
    }

    const files = await listSystemFiles()
    return NextResponse.json(files)
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Failed to inspect files" }, { status: 500 })
  }
}
