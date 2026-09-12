import { NextRequest, NextResponse } from "next/server"
import { getChannelMessages, sendMessage } from "@/lib/slack-client"

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const channelId = searchParams.get("channel_id") || "C019"
    const data = await getChannelMessages(channelId)
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { channel_id, text } = body
    if (!channel_id || !text) {
      return NextResponse.json({ error: "Missing channel_id or text" }, { status: 400 })
    }
    const data = await sendMessage(channel_id, text)
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
