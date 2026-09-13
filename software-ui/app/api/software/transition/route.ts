import { NextRequest, NextResponse } from "next/server"
import { transitionEntity } from "@/lib/software-client"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { entity_name, entity_id, action, fields } = body
    const res = await transitionEntity(entity_name, entity_id, action, fields || {})
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
