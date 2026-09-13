import { NextRequest, NextResponse } from 'next/server';
import { runEnterpriseBridge } from '@/lib/enterprise-client';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status') || '';

    const res = await runEnterpriseBridge('list_approvals', [status]);
    return NextResponse.json(res);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, requestId, decision, notes, requestType, approverId, amountUsd, reason } = body;

    if (action === 'decide') {
      const res = await runEnterpriseBridge('decide_approval', [requestId, decision, notes || '']);
      return NextResponse.json(res);
    }

    if (action === 'request') {
      const res = await runEnterpriseBridge('request_approval', [
        requestType,
        approverId,
        String(amountUsd),
        reason,
      ]);
      return NextResponse.json(res);
    }

    return NextResponse.json({ error: `Unsupported action: ${action}` }, { status: 400 });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
