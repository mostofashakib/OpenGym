import { NextResponse } from "next/server"
import { getSchema, listDomains } from "@/lib/software-client"

export async function GET() {
  try {
    const [schemaRes, domainsRes] = await Promise.all([getSchema(), listDomains()])
    return NextResponse.json({
      ok: true,
      schema: schemaRes?.schema || {},
      layout: schemaRes?.layout || "sidebar_table",
      domain: schemaRes?.domain || "logistics",
      split: schemaRes?.split || "iid",
      domains: domainsRes?.domains || [],
      splits: domainsRes?.splits || [],
    })
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
