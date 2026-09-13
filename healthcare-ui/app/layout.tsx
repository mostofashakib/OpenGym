import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Aegis Health | Clinical EHR System',
  description: 'Enterprise clinical electronic health records suite with FHIR data models, medication safety invariants, and HIPAA compliance audit',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              window.__OPENGYM_VIRTUAL_EPOCH__ = 1792054800000;
              (function() {
                const fixedEpoch = 1792054800000;
                const Orig = Date;
                function FakeDate(...args) {
                  if (args.length === 0) return new Orig(fixedEpoch);
                  return new Orig(...args);
                }
                FakeDate.now = () => fixedEpoch;
                FakeDate.parse = Orig.parse;
                FakeDate.UTC = Orig.UTC;
                FakeDate.prototype = Orig.prototype;
                window.Date = FakeDate;
              })();
            `,
          }}
        />
      </head>
      <body className="antialiased bg-[#090d16] text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
