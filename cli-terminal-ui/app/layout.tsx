import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "OpenGym Cloud Console | app-node-04.prod.corp",
  description: "Enterprise DevOps Terminal and Incident Remediation Console",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090d16] text-slate-100 antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
        {children}
      </body>
    </html>
  )
}
