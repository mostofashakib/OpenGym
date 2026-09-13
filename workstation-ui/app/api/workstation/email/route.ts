import { NextRequest, NextResponse } from "next/server"
import { listEmails, getEmailThread, sendEmail } from "@/lib/workstation-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const threadId = searchParams.get("threadId")
  const folder = searchParams.get("folder") || "inbox"
  const query = searchParams.get("q") || ""

  try {
    if (threadId) {
      const res = await getEmailThread(threadId)
      return NextResponse.json(res)
    }
    const res = await listEmails(folder, query)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { to, subject, body: content } = body
    const res = await sendEmail(to, subject, content)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
