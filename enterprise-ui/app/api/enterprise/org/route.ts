import { NextRequest, NextResponse } from 'next/server';
import { runEnterpriseBridge } from '@/lib/enterprise-client';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const employeeId = searchParams.get('id');
    const query = searchParams.get('q') || '';
    const dept = searchParams.get('dept') || '';

    if (employeeId) {
      const res = await runEnterpriseBridge('get_employee', [employeeId]);
      return NextResponse.json(res);
    }

    const res = await runEnterpriseBridge('list_org', [query, dept]);
    return NextResponse.json(res);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
