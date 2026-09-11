"use client"

import type React from "react"
import { useEffect, useMemo } from "react"
import { useRandomization } from "@/lib/randomization-context"

export function ThemeVars({ children }: { children: React.ReactNode }) {
  const r = useRandomization() 
  const p = r?.themePalette 
  const vars = useMemo(() => ({
    "--app-bg": p?.bg || "#FFFFFF",
    "--app-surface": p?.surface || "#F5F5F5",
    "--app-surface-hover": p?.surfaceHover || "#E5E7EB",
    "--app-text": p?.text || "#111827",
    "--app-text-muted": p?.textMuted || "#6B7280",
    "--app-border": p?.border || "#E5E7EB",
    "--app-primary": p?.primary || "#2563EB",
    "--app-primary-hover": p?.primaryHover || "#1D4ED8",
    // Also map to existing design tokens used in globals.css (Tailwind theme)
    "--background": p?.bg || "#FFFFFF",
    "--foreground": p?.text || "#111827",
    "--card": p?.surface || "#FFFFFF",
    "--card-foreground": p?.text || "#111827",
    "--popover": p?.surface || "#FFFFFF",
    "--popover-foreground": p?.text || "#111827",
    "--primary": p?.primary || "#2563EB",
    "--primary-foreground": "#FFFFFF",
    "--secondary": p?.surface || "#F3F4F6",
    "--secondary-foreground": p?.text || "#111827",
    "--muted": p?.surface || "#F3F4F6",
    "--muted-foreground": p?.textMuted || "#6B7280",
    "--accent": p?.surface || "#F3F4F6",
    "--accent-foreground": p?.text || "#111827",
    "--destructive": "#DC2626",
    "--destructive-foreground": "#FFFFFF",
    "--border": p?.border || "#E5E7EB",
    "--input": p?.border || "#E5E7EB",
    "--ring": p?.primary || "#2563EB",
  }), [p])

  useEffect(() => {
    const el = document.documentElement
    const prev: Array<[string, string]> = []
    for (const [k, v] of Object.entries(vars)) {
      prev.push([k, el.style.getPropertyValue(k)])
      el.style.setProperty(k, v)
    }
    const prevTheme = el.getAttribute("data-theme") || ""
    const isDark = typeof (r?.themePalette?.name) === "string" && /dark/i.test(r.themePalette.name)
    el.setAttribute("data-theme", isDark ? "dark" : "light")
    return () => {
      for (const [k, v] of prev) el.style.setProperty(k, v)
      el.setAttribute("data-theme", prevTheme)
    }
  }, [vars])

  return <>{children}</>
}


