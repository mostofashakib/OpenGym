#!/usr/bin/env node
/* eslint-disable no-console */
const fs = require("fs")
const path = require("path")

function generateRandomization() {
  return {
    sidebar: {
      collapsed: randomBoolean(),
    },
    layout: {
      headerPosition: randomChoice(["top", "side"]),
    },
    appName: pickAppName(),
    appLogo: pickAppLogo(),
    sidebarLabels: pickSidebarLabels(),
    searchInput: pickSearchInput(),
    sidebarFolderOrder: pickFolderOrder(),
    themePalette: pickThemePalette(),
    threadIcons: pickThreadIcons(),
    threadOpenMode: pickThreadOpenMode(),
    selectionToolbar: pickSelectionToolbar(),
    emailListView: pickEmailListView(),
    emailListItemOrder: pickEmailListItemOrder(),
  }
}

function randomBoolean() {
  return Math.random() < 0.5
}

function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function pickSidebarLabels() {
  const labels = {
    compose: randomChoice(["Compose", "New message", "Write" ]),
    inbox: randomChoice(["Inbox", "Primary", "Mail" ]),
    starred: randomChoice(["Starred", "Favorites", "Pinned" ]),
    snoozed: randomChoice(["Snoozed", "Later", "Remind me" ]),
    sent: randomChoice(["Sent", "Outbox", "Dispatched" ]),
    drafts: randomChoice(["Drafts", "In progress"]),
    important: randomChoice(["Important", "Priority", "Focus" ]),
    all: randomChoice(["All Mail", "Everything" ]),
    spam: randomChoice(["Spam", "Junk" ]),
    trash: randomChoice(["Trash", "Bin", "Deleted" ]),
  }
  return labels
}

function pickSearchInput() {
  const placeholders = [
    "Search mail",
    "Find messages",
    "Look up emails",
    "Type to search",
    "Search inbox",
  ]
  const align = randomChoice(["left", "center", "right"]) // affects wrapper alignment and text align
  const widthClass = randomChoice(["max-w-md", "max-w-lg", "max-w-xl", "max-w-2xl"]) // wrapper max width
  const paddingVariant = randomChoice(["compact", "cozy", "roomy"]) // input padding presets
  const padding = {
    compact: { pl: "pl-9", pr: "pr-10" },
    cozy: { pl: "pl-10", pr: "pr-12" },
    roomy: { pl: "pl-12", pr: "pr-14" },
  }[paddingVariant]
  const textAlignClass = align === "center" ? "text-center" : align === "right" ? "text-right" : "text-left"
  const marginClass = align === "center" ? "mx-auto" : align === "right" ? "ml-auto" : "mr-auto"
  const mode = randomChoice(["expanded", "icon"]) // whether to show input by default or icon that expands
  return {
    placeholder: randomChoice(placeholders),
    align,
    widthClass,
    paddingLeftClass: padding.pl,
    paddingRightClass: padding.pr,
    textAlignClass,
    marginClass,
    mode,
  }
}

function pickAppName() {
  const names = [
    "PostBird",
    "MailSprout",
    "Inboxly",
    "QuillMail",
    "CourierCat",
    "Letterfox",
    "ParcelPost",
    "NimbusMail",
    "SwiftInbox",
    "EchoMail",
  ]
  return randomChoice(names)
}

// Distinct logo styles keyed for client rendering
function pickAppLogo() {
  return randomChoice(["envelope", "paperplane", "spark", "quill", "orb"]) // client chooses SVG variant
}

function pickFolderOrder() {
  const ids = ["inbox","starred","snoozed","sent","drafts","important","all","spam","trash"]
  const arr = ids.slice()
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

function pickThemePalette() {
  const light = [
    {
      name: "blue",
      primary: "#2563EB",
      primaryHover: "#1D4ED8",
      bg: "#F8FAFF",
      surface: "#F3F4F6",
      surfaceHover: "#E5E7EB",
      text: "#111827",
      textMuted: "#4B5563",
      border: "#E5E7EB",
    },
    {
      name: "teal",
      primary: "#0D9488",
      primaryHover: "#0F766E",
      bg: "#F7FFFD",
      surface: "#F0FDFA",
      surfaceHover: "#CCFBF1",
      text: "#0F172A",
      textMuted: "#475569",
      border: "#E2E8F0",
    },
    {
      name: "purple",
      primary: "#7C3AED",
      primaryHover: "#6D28D9",
      bg: "#FAF8FF",
      surface: "#F5F3FF",
      surfaceHover: "#EDE9FE",
      text: "#111827",
      textMuted: "#4B5563",
      border: "#E5E7EB",
    },
    {
      name: "slate",
      primary: "#475569",
      primaryHover: "#334155",
      bg: "#F8FAFC",
      surface: "#F1F5F9",
      surfaceHover: "#E2E8F0",
      text: "#0F172A",
      textMuted: "#475569",
      border: "#E2E8F0",
    },
    {
      name: "amber",
      primary: "#D97706",
      primaryHover: "#B45309",
      bg: "#FFFEF5",
      surface: "#FFFBEB",
      surfaceHover: "#FEF3C7",
      text: "#111827",
      textMuted: "#4B5563",
      border: "#E5E7EB",
    },
  ]
  const dark = [
    {
      name: "midnight-dark",
      primary: "#60A5FA",
      primaryHover: "#3B82F6",
      bg: "#0B1220",
      surface: "#111827",
      surfaceHover: "#1F2937",
      text: "#F9FAFB",
      textMuted: "#9CA3AF",
      border: "#374151",
    },
    {
      name: "emerald-dark",
      primary: "#34D399",
      primaryHover: "#10B981",
      bg: "#0C1512",
      surface: "#0F1C18",
      surfaceHover: "#11211C",
      text: "#E5F9F1",
      textMuted: "#9CA3AF",
      border: "#1F3A2E",
    },
    {
      name: "violet-dark",
      primary: "#A78BFA",
      primaryHover: "#8B5CF6",
      bg: "#0F0D1A",
      surface: "#17132B",
      surfaceHover: "#1E173B",
      text: "#F4F3FF",
      textMuted: "#A3A3B2",
      border: "#2E2A45",
    },
    {
      name: "slate-dark",
      primary: "#93C5FD",
      primaryHover: "#60A5FA",
      bg: "#0B1220",
      surface: "#0F172A",
      surfaceHover: "#172036",
      text: "#E5E7EB",
      textMuted: "#9CA3AF",
      border: "#1F2937",
    },
  ]
  // 50/50 random pick between light and dark families
  return Math.random() < 0.5 ? randomChoice(dark) : randomChoice(light)
}

function pickThreadIcons() {
  return {
    star: randomChoice(["star"]),
    archive: randomChoice(["archive"]),
    trash: randomChoice(["trash", "trash2"]),
  }
}

function pickThreadOpenMode() {
  return randomBoolean() ? "modal" : "page"
}

function pickEmailListView() {
  // Alternate between classic list rows and a grid card view
  return randomChoice(["list", "grid"]) // default remains list
}

function pickSelectionToolbar() {
  return {
    paginationPosition: randomChoice(["top", "bottom"]),
  }
}

function pickEmailListItemOrder() {
  const base = ["sender", "message", "time"]
  // simple shuffle
  const arr = base.slice()
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

function main() {
  const projectRoot = path.resolve(__dirname, "..")
  const outDir = path.join(projectRoot, "generated")
  const outFile = path.join(outDir, "randomization.json")
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true })
  const data = generateRandomization()
  console.log(data)
  const json = JSON.stringify(data, null, 2) + "\n"
  fs.writeFileSync(outFile, json, "utf8")
  console.log(`[randomization] wrote ${path.relative(projectRoot, outFile)}`)

  // Also mirror to public so it can be fetched at /generated/randomization.json in dev
  const publicDir = path.join(projectRoot, "public", "generated")
  if (!fs.existsSync(publicDir)) fs.mkdirSync(publicDir, { recursive: true })
  const publicFile = path.join(publicDir, "randomization.json")
  fs.writeFileSync(publicFile, json, "utf8")
  console.log(`[randomization] copied to ${path.relative(projectRoot, publicFile)}`)

  // Emit a .d.ts that stays in sync with the generated object (structure-wise)
  const typesDir = path.join(projectRoot, "lib")
  const typesOutFile = path.join(typesDir, "app-randomization.d.ts")
  if (!fs.existsSync(typesDir)) {
    fs.mkdirSync(typesDir, { recursive: true })
  }
  const header =
    `/*
Auto-generated from scripts/generate_randomization.js. Do not edit manually.
Edits will be overwritten the next time the generator runs.
*/\n`
  const typeBody = emitTypeDeclaration("AppRandomization", data)
  fs.writeFileSync(typesOutFile, header + typeBody + "\n", "utf8")
  console.log(`[randomization] types updated ${path.relative(projectRoot, typesOutFile)}`)
}

if (require.main === module) {
  try { main() } catch (e) { console.error(e); process.exit(1) }
}

module.exports = { generateRandomization }



// --- helpers to generate a .d.ts from a JS object shape ---
function emitTypeDeclaration(rootName, value) {
  return `export type ${rootName} = ${toTsType(value, 0)}\n`
}

function toTsType(value, indentLevel) {
  const indent = (n) => "  ".repeat(n)
  if (value === null) return "null"
  const t = typeof value
  if (t === "string") return "string"
  if (t === "number") return "number"
  if (t === "boolean") return "boolean"
  if (Array.isArray(value)) {
    // Infer the element type from the first item if available; default to unknown
    const elemType = value.length > 0 ? toTsType(value[0], indentLevel) : "unknown"
    return `${elemType}[]`
  }
  if (t === "object") {
    const keys = Object.keys(value).sort()
    if (keys.length === 0) return "Record<string, unknown>"
    const fields = keys
      .map((k) => {
        const v = value[k]
        const safeKey = /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(k) ? k : JSON.stringify(k)
        return `${indent(indentLevel + 1)}${safeKey}: ${toTsType(v, indentLevel + 1)}`
      })
      .join("\n")
    return `{\n${fields}\n${indent(indentLevel)}}`
  }
  return "unknown"
}