import { NextRequest, NextResponse } from "next/server"
import { getThreadReplies, sendThreadReply } from "@/lib/slack-client"

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const threadTs = searchParams.get("thread_ts")
    const channelId = searchParams.get("channel_id") || "C019"
    if (!threadTs) {
      return NextResponse.json({ error: "Missing thread_ts" }, { status: 400 })
    }
    const data = await getThreadReplies(threadTs, channelId)
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { channel_id, thread_ts, text } = body
    if (!channel_id || !thread_ts || !text) {
      return NextResponse.json({ error: "Missing channel_id, thread_ts, or text" }, { status: 400 })
    }
    const data = await sendThreadReply(channel_id, thread_ts, text)
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
