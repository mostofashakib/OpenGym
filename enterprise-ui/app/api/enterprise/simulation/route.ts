import { NextRequest, NextResponse } from 'next/server';
import { runEnterpriseBridge } from '@/lib/enterprise-client';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, minutes, summary, affectedIds } = body;

    if (action === 'step') {
      const res = await runEnterpriseBridge('step_simulation', [String(minutes || 15)]);
      return NextResponse.json(res);
    }

    if (action === 'submit') {
      const res = await runEnterpriseBridge('submit_task', [
        summary || 'Task completed',
        affectedIds || '',
      ]);
      return NextResponse.json(res);
    }

    return NextResponse.json({ error: `Unsupported simulation action: ${action}` }, { status: 400 });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
