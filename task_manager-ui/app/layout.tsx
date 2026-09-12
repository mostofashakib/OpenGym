import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Titanium Enterprise Tracker | Release Gate Console",
  description: "Enterprise issue tracking and cutover milestone gate management console",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className="h-screen w-screen bg-[#0d1117] text-[#e6edf3] flex flex-col overflow-hidden">
        {children}
      </body>
    </html>
  )
}
