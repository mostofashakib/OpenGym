import { NextRequest, NextResponse } from "next/server"
import { addReaction } from "@/lib/slack-client"

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { channel_id, ts, emoji } = body
    if (!channel_id || !ts || !emoji) {
      return NextResponse.json({ error: "Missing channel_id, ts, or emoji" }, { status: 400 })
    }
    const data = await addReaction(channel_id, ts, emoji)
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
