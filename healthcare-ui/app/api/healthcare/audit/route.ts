import { NextRequest, NextResponse } from "next/server"
import { getAuditEvents, getStateHash } from "@/lib/healthcare-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const patientId = searchParams.get("patientId") || ""

  try {
    const [auditRes, hashRes] = await Promise.all([getAuditEvents(patientId), getStateHash()])
    return NextResponse.json({
      ok: true,
      audit_events: auditRes?.audit_events || [],
      state_hash: hashRes?.state_hash || "unknown",
    })
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
