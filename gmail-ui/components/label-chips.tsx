import { Badge } from "@/components/ui/badge"

interface LabelMeta {
  id: string
  name: string
  type: "SYSTEM" | "USER"
  color?: string
}

interface LabelChipsProps {
  labels?: string[]
  labelMetaById?: Record<string, LabelMeta>
  showInboxLabelChip?: boolean
  className?: string
}

export function LabelChips({ labels, labelMetaById, showInboxLabelChip, className }: LabelChipsProps) {
  if (!labels || labels.length === 0) return null

  const filtered = labels.filter((labelId) => {
    const meta = labelMetaById?.[labelId]
    const upper = (labelId || "").toUpperCase()
    const isSystem = meta
      ? meta.type === "SYSTEM"
      : [
          "INBOX",
          "SENT",
          "DRAFTS",
          "TRASH",
          "ARCHIVE",
          "SPAM",
          "STARRED",
          "IMPORTANT",
        ].includes(upper)
    if (showInboxLabelChip && upper === "INBOX") return true
    return !isSystem
  })

  if (filtered.length === 0) return null

  return (
    <div className={`flex flex-wrap gap-1 ${className || ""}`}>
      {filtered.map((labelId) => {
        const meta = labelMetaById?.[labelId]
        const display = meta?.name || labelId
        const color = typeof meta?.color === "string" ? (meta.color as string) : undefined
        const isHex = typeof color === "string" && color.trim().startsWith("#")
        const hex = (color || "").replace("#", "")
        const r = parseInt(hex.substring(0, 2) || "AA", 16)
        const g = parseInt(hex.substring(2, 4) || "AA", 16)
        const b = parseInt(hex.substring(4, 6) || "AA", 16)
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        const textColor = luminance > 0.6 ? "#111827" : "#F9FAFB"

        return (
          <Badge
            key={labelId}
            variant="secondary"
            className={`text-xs hover:opacity-90 transition-colors ${!isHex && color ? color : "bg-gray-200 "}`}
            style={isHex ? { backgroundColor: color, color: textColor, borderColor: color } : undefined}
          >
            <span className="injectable">{display}</span>
          </Badge>
        )
      })}
    </div>
  )
}


