import { NextRequest, NextResponse } from "next/server"
import { listPatients, getPatientChart, verifyPatient } from "@/lib/healthcare-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const patientId = searchParams.get("id")
  const query = searchParams.get("q") || ""

  try {
    if (patientId) {
      const res = await getPatientChart(patientId)
      return NextResponse.json(res)
    }
    const res = await listPatients(query)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { identifier, dob } = body
    const res = await verifyPatient(identifier, dob || "")
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
