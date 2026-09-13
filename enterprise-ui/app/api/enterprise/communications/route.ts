import { NextRequest, NextResponse } from 'next/server';
import { runEnterpriseBridge } from '@/lib/enterprise-client';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const email = searchParams.get('email') || 'support-team@apexcorp.internal';

    const res = await runEnterpriseBridge('read_inbox', [email]);
    return NextResponse.json(res);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { sender, recipients, subject, emailBody } = body;

    const res = await runEnterpriseBridge('send_email', [
      sender,
      Array.isArray(recipients) ? recipients.join(',') : recipients,
      subject,
      emailBody,
    ]);
    return NextResponse.json(res);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
