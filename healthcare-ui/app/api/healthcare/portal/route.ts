import { NextRequest, NextResponse } from "next/server"
import { sendPortalMessage, escalateEmergency } from "@/lib/healthcare-client"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, patient_id, subject, body: content, priority, reason, vitals } = body

    if (action === "escalate") {
      const res = await escalateEmergency(patient_id, reason, vitals)
      return NextResponse.json(res)
    } else {
      const res = await sendPortalMessage(patient_id, subject, content, priority || "routine")
      return NextResponse.json(res)
    }
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
