import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "ProcureCorp Portal | Enterprise Procurement & Compliance",
  description: "Enterprise purchase orders, vendor risk management, and compliance auditing portal",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0b0f19] text-slate-100 antialiased selection:bg-sky-500/30 selection:text-sky-200">
        {children}
      </body>
    </html>
  )
}
