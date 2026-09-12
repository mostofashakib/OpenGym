"use client"

import type React from "react"
import { createContext, useContext, useEffect, useMemo, useState } from "react"
import type { AppRandomization } from "@/lib/app-randomization"

const RandomizationContext = createContext<AppRandomization | null>(null)


export function RandomizationProvider({ children }: { children: React.ReactNode }) {
  const [value, setValue] = useState<AppRandomization | null>(null)

  useEffect(() => {
    let cancelled = false
    async function maybeLoadGenerated() {
      try {
        const res = await fetch("/generated/randomization.json", { cache: "no-store" })
        if (!res.ok) return
        const data = (await res.json()) as AppRandomization
        if (!cancelled) setValue(data)
      } catch {
        // ignore; fall back to default randomization
      }
    }
    maybeLoadGenerated()
    return () => {
      cancelled = true
    }
  }, [])

  const memoized = useMemo<AppRandomization | null>(() => value, [value])
  return <RandomizationContext.Provider value={memoized}>{children}</RandomizationContext.Provider>
}

export function useRandomization(): AppRandomization | null {
  const ctx = useContext(RandomizationContext)
  return ctx!
}


