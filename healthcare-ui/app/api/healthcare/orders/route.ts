import { NextRequest, NextResponse } from "next/server"
import { createClinicalOrder, updateOrder } from "@/lib/healthcare-client"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, patient_id, order_type, code, display, dosage, instructions, is_stat, order_id, status, notes } = body

    if (action === "update") {
      const res = await updateOrder(order_id, status, notes || "")
      return NextResponse.json(res)
    } else {
      const res = await createClinicalOrder(
        patient_id,
        order_type || "medication",
        code || "RX-GENERIC",
        display || "Medication Order",
        dosage || "",
        instructions || "",
        Boolean(is_stat)
      )
      return NextResponse.json(res)
    }
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
