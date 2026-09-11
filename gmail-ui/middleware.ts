import { NextRequest, NextResponse } from 'next/server';
import { UAParser } from 'ua-parser-js';

// Fun, agent-themed basic auth defaults. Can be overridden via env vars.
const BASIC_AUTH_USERNAME = process.env.BASIC_AUTH_USERNAME || 'agent';
const BASIC_AUTH_PASSWORD = process.env.BASIC_AUTH_PASSWORD || 'we-love-cua!';

function isRequestFromBrowser(request: NextRequest): boolean {
  const userAgentHeader = request.headers.get('user-agent') || '';
  const parser = new UAParser(userAgentHeader);
  const browser = parser.getBrowser();
  // If UAParser identifies a browser name, it's likely a real browser.
  return Boolean(browser && browser.name);
}

function isBasicAuthValid(request: NextRequest): boolean {
  const authHeader = request.headers.get('authorization') || '';
  if (!authHeader || !authHeader.toLowerCase().startsWith('basic ')) {
    return false;
  }

  try {
    const base64Credentials = authHeader.slice(6).trim();
    // atob is available in the Edge runtime
    const decoded = atob(base64Credentials);
    const separatorIndex = decoded.indexOf(':');
    if (separatorIndex === -1) {
      return false;
    }
    const username = decoded.slice(0, separatorIndex);
    const password = decoded.slice(separatorIndex + 1);
    return username === BASIC_AUTH_USERNAME && password === BASIC_AUTH_PASSWORD;
  } catch (_err) {
    return false;
  }
}

export function middleware(request: NextRequest) {
  if (process.env.DISABLE_AUTH === '1' || process.env.DISABLE_AUTH === 'true') {
    return NextResponse.next();
  }
  const allowed = isRequestFromBrowser(request) || isBasicAuthValid(request);
  if (allowed) {
    return NextResponse.next();
  }

  return new NextResponse('Missing or invalid authentication', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Agent Playground", charset="UTF-8"',
      'Cache-Control': 'no-store',
    },
  });
}

// Skip static assets and Next internals for performance and to avoid unnecessary challenges.
export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|images/|.*\\.(?:png|jpg|jpeg|gif|webp|svg|ico)$).*)',
  ],
};


