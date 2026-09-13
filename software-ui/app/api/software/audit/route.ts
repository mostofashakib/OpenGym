import { NextResponse } from "next/server"
import { getAuditLog, getStateHash } from "@/lib/software-client"

export async function GET() {
  try {
    const [auditRes, hashRes] = await Promise.all([getAuditLog(), getStateHash()])
    return NextResponse.json({
      ok: true,
      audit_log: auditRes?.audit_log || [],
      state_hash: hashRes?.state_hash || "unknown",
    })
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
