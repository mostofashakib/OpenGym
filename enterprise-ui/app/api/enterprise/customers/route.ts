import { NextRequest, NextResponse } from 'next/server';
import { runEnterpriseBridge } from '@/lib/enterprise-client';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const customerId = searchParams.get('id');
    const query = searchParams.get('q') || '';

    if (customerId) {
      const res = await runEnterpriseBridge('get_customer_profile', [customerId]);
      return NextResponse.json(res);
    }

    const res = await runEnterpriseBridge('list_customers', [query]);
    return NextResponse.json(res);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
