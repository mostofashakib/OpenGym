import { NextResponse } from "next/server"
import { listChannels } from "@/lib/slack-client"

export async function GET() {
  try {
    const data = await listChannels()
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
