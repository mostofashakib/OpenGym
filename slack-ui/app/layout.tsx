import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Acme Slack Workspace | Engineering",
  description: "Enterprise Slack communication client and agent environment",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className="h-screen w-screen bg-[#1a1d21] text-[#d1d2d3] flex flex-col overflow-hidden">
        {children}
      </body>
    </html>
  )
}
