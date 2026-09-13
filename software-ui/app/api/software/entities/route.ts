import { NextRequest, NextResponse } from "next/server"
import { searchEntities, getEntity, createEntity, updateEntity } from "@/lib/software-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const entityName = searchParams.get("entity") || "Shipment"
  const entityId = searchParams.get("id")
  const query = searchParams.get("q") || ""
  const page = parseInt(searchParams.get("page") || "1", 10)
  const pageSize = parseInt(searchParams.get("pageSize") || "25", 10)

  try {
    if (entityId) {
      const res = await getEntity(entityName, entityId)
      return NextResponse.json(res)
    }
    const res = await searchEntities(entityName, query, null, page, pageSize)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, entity_name, entity_id, fields } = body

    if (action === "update") {
      const res = await updateEntity(entity_name, entity_id, fields)
      return NextResponse.json(res)
    } else {
      const res = await createEntity(entity_name, fields)
      return NextResponse.json(res)
    }
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
