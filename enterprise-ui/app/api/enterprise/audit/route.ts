import { NextRequest, NextResponse } from 'next/server';
import { runEnterpriseBridge } from '@/lib/enterprise-client';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const actor = searchParams.get('actor') || '';
    const action = searchParams.get('action') || '';
    const fetchHash = searchParams.get('hash') === 'true';

    if (fetchHash) {
      const hashRes = await runEnterpriseBridge('state_hash');
      return NextResponse.json(hashRes);
    }

    const auditRes = await runEnterpriseBridge('get_audit_log', [actor, action]);
    return NextResponse.json(auditRes);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
