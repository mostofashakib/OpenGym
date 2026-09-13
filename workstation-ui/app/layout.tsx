import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "OmniDesk | Employee Workstation OS",
  description: "Simulated enterprise employee desktop workstation environment for autonomous computer-use agents",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
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
      <body className="h-screen w-screen bg-[#0b1120] text-slate-100 flex flex-col overflow-hidden">
        {children}
      </body>
    </html>
  )
}
