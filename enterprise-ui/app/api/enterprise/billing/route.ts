import { NextRequest, NextResponse } from 'next/server';
import { runEnterpriseBridge } from '@/lib/enterprise-client';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const customerId = searchParams.get('customerId') || '';

    const res = await runEnterpriseBridge('get_invoices', [customerId]);
    return NextResponse.json(res);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { invoiceId, customerId, amountUsd, reason, approvedById } = body;

    const res = await runEnterpriseBridge('process_refund', [
      invoiceId,
      customerId,
      String(amountUsd),
      reason || 'Customer refund',
      approvedById || '',
    ]);
    return NextResponse.json(res);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
