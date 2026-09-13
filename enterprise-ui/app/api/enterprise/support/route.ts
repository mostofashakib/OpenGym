import { NextRequest, NextResponse } from 'next/server';
import { runEnterpriseBridge } from '@/lib/enterprise-client';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const ticketId = searchParams.get('id');
    const status = searchParams.get('status') || '';

    if (ticketId) {
      const res = await runEnterpriseBridge('get_ticket', [ticketId]);
      return NextResponse.json(res);
    }

    const res = await runEnterpriseBridge('list_tickets', [status]);
    return NextResponse.json(res);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, ticketId, content, isInternal, status } = body;

    if (action === 'add_comment') {
      const res = await runEnterpriseBridge('add_comment', [ticketId, content, String(!!isInternal)]);
      return NextResponse.json(res);
    }

    if (action === 'update_status') {
      const res = await runEnterpriseBridge('update_ticket_status', [ticketId, status]);
      return NextResponse.json(res);
    }

    return NextResponse.json({ error: `Unsupported action: ${action}` }, { status: 400 });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
