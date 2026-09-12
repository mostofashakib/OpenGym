export function isFixedClockEnabled(): boolean {
  try {
    const raw = process.env.NEXT_PUBLIC_FIXED_TIME_ENABLED
    if (raw === undefined || raw === null || String(raw).trim() === "") return true
    return String(raw).toLowerCase() === "true"
  } catch {
    return true
  }
}

export function getFixedEpoch(): number | null {
  try {
    const iso = String(process.env.NEXT_PUBLIC_FIXED_TIME_ISO || "2030-03-14T03:14:00-05:00")
    const t = Date.parse(iso)
    return Number.isFinite(t) ? t : null
  } catch {
    return null
  }
}

export function nowDate(): Date {
  const enabled = isFixedClockEnabled()
  const epoch = getFixedEpoch()
  if (enabled && epoch !== null) {
    return new Date(epoch)
  }
  return new Date()
}

export function nowTs(): number {
  const enabled = isFixedClockEnabled()
  const epoch = getFixedEpoch()
  if (enabled && epoch !== null) {
    return epoch
  }
  return Date.now()
}


// Snooze helpers (use fixed clock when configured)
// Fixed-zone math: assume the mock location (America/Chicago) everywhere on the client
function getFixedOffsetMinutes(): number {
  try {
    const iso = String(process.env.NEXT_PUBLIC_FIXED_TIME_ISO || "2030-03-14T03:14:00-05:00")
    const m = iso.match(/([+-])(\d{2}):(\d{2})$/)
    if (m) {
      const sign = m[1] === "-" ? -1 : 1
      const hh = parseInt(m[2], 10)
      const mm = parseInt(m[3], 10)
      return sign * (hh * 60 + mm)
    }
  } catch {}
  return -300 // default to UTC-5 (Austin/CDT)
}

function getZoneLocal(ts: number): Date {
  const off = getFixedOffsetMinutes()
  return new Date(ts + off * 60_000)
}

function buildFixedZonedISO(y: number, m1: number, d: number, hh: number, mm = 0, ss = 0): string {
  const off = getFixedOffsetMinutes()
  const utcMs = Date.UTC(y, m1 - 1, d, hh, mm, ss) - off * 60_000
  return new Date(utcMs).toISOString()
}

export function snoozeLaterTodayISO(): string {
  const znow = getZoneLocal(nowTs())
  const y = znow.getUTCFullYear()
  const m = znow.getUTCMonth() + 1
  let d = znow.getUTCDate()
  const hour = znow.getUTCHours()
  const min = znow.getUTCMinutes()
  const alreadyPast = hour > 18 || (hour === 18 && min > 0)
  if (alreadyPast) d += 1
  return buildFixedZonedISO(y, m, d, 18, 0, 0)
}

export function snoozeTomorrowISO(): string {
  const znow = getZoneLocal(nowTs())
  const y = znow.getUTCFullYear()
  const m = znow.getUTCMonth() + 1
  const d = znow.getUTCDate() + 1
  return buildFixedZonedISO(y, m, d, 8, 0, 0)
}

export function snoozeThisWeekendISO(): string {
  const znow = getZoneLocal(nowTs())
  const y = znow.getUTCFullYear()
  const m = znow.getUTCMonth() + 1
  let d = znow.getUTCDate()
  const day = znow.getUTCDay() // 0=Sun..6=Sat for zone-local
  if (day === 6) {
    // Saturday: if before 8 AM use today 8 AM; else next Saturday 8 AM
    const hour = znow.getUTCHours()
    const min = znow.getUTCMinutes()
    if (hour < 8 || (hour === 8 && min === 0)) return buildFixedZonedISO(y, m, d, 8, 0, 0)
    d += 7
    return buildFixedZonedISO(y, m, d, 8, 0, 0)
  }
  const daysUntilSaturday = (6 - day + 7) % 7 || 7
  d += daysUntilSaturday
  return buildFixedZonedISO(y, m, d, 8, 0, 0)
}

export function snoozeNextWeekISO(): string {
  const znow = getZoneLocal(nowTs())
  const y = znow.getUTCFullYear()
  const m = znow.getUTCMonth() + 1
  let d = znow.getUTCDate()
  const day = znow.getUTCDay() // 1=Mon
  if (day === 1) {
    const hour = znow.getUTCHours()
    const min = znow.getUTCMinutes()
    if (hour < 8 || (hour === 8 && min === 0)) return buildFixedZonedISO(y, m, d, 8, 0, 0)
    d += 7
    return buildFixedZonedISO(y, m, d, 8, 0, 0)
  }
  const daysUntilMonday = (1 - day + 7) % 7 || 7
  d += daysUntilMonday
  return buildFixedZonedISO(y, m, d, 8, 0, 0)
}

export function buildFixedZonedISOFromInputs(datePart: string, timePart: string): string {
  try {
    const [y, mo, da] = datePart.split("-").map((x) => parseInt(x, 10))
    const [hh, mi] = timePart.split(":" ).map((x) => parseInt(x, 10))
    if (!Number.isFinite(y) || !Number.isFinite(mo) || !Number.isFinite(da) || !Number.isFinite(hh) || !Number.isFinite(mi)) {
      throw new Error("bad inputs")
    }
    return buildFixedZonedISO(y, mo, da, hh, mi, 0)
  } catch {
    // Fallback: interpret as local, then convert
    return new Date(`${datePart}T${timePart}:00`).toISOString()
  }
}


