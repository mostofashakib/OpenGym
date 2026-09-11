"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  Plus,
  Inbox,
  Star,
  Send,
  FileText,
  Users,
  AlertCircle,
  Trash2,
  Tag,
  ChevronDown,
  ChevronRight,
  Clock,
} from "lucide-react"
import { useEffect, useState } from "react"
import { useRandomization } from "@/lib/randomization-context"

interface Email {
  id: string
  sender: string
  subject: string
  preview: string
  time: string
  isRead: boolean
  isStarred: boolean
  isImportant: boolean
  hasAttachment?: boolean
  labels?: string[]
}

interface SidebarNavigationProps {
  ispsed: boolean
  currentFolder: string
  emails: Email[]
  folderUnreadCounts?: Record<string, number>
  labelUnreadCounts?: Record<string, number>
  labels?: Array<{ id: string; name: string; color?: string }>
  onFolderChange: (folder: string) => void
  onCompose: () => void
  onCreateLabel?: () => void | Promise<void>
  position?: "side" | "top"
}

// folders are defined within the component to allow referencing locally-defined icons

export function SidebarNavigation({
  ispsed,
  currentFolder,
  emails,
  folderUnreadCounts,
  labelUnreadCounts,
  labels,
  onFolderChange,
  onCompose,
  onCreateLabel,
  position = "side",
}: SidebarNavigationProps) {
  const [showLabels, setShowLabels] = useState(false)
  const randomization = useRandomization()
  const names = {
    // Defaults mirror committed generated/randomization.json to avoid SSR/client mismatch
    compose: randomization?.sidebarLabels?.compose || "Compose",
    inbox: randomization?.sidebarLabels?.inbox || "Primary",
    starred: randomization?.sidebarLabels?.starred || "Starred",
    snoozed: randomization?.sidebarLabels?.snoozed || "Later",
    sent: randomization?.sidebarLabels?.sent || "Dispatched",
    drafts: randomization?.sidebarLabels?.drafts || "In progress",
    important: randomization?.sidebarLabels?.important || "Focus",
    all: randomization?.sidebarLabels?.all || "Everything",
    spam: randomization?.sidebarLabels?.spam || "Spam",
    trash: randomization?.sidebarLabels?.trash || "Trash",
  }

  const ImportantIcon = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path
        d="M2.25 3.25h7.1l4.4 4.75-4.4 4.75h-7.1c-.69 0-1.25-.56-1.25-1.25V4.5c0-.69.56-1.25 1.25-1.25z"
        fill="currentColor"
        stroke="currentColor"
        strokeWidth="1"
        strokeLinejoin="round"
      />
    </svg>
  )

  const folders = [
    { id: "inbox", name: names.inbox, icon: Inbox, color: "text-red-700", bgColor: "bg-red-100" },
    { id: "starred", name: names.starred, icon: Star, color: "text-gray-700", bgColor: "" },
    { id: "snoozed", name: names.snoozed, icon: Clock, color: "text-gray-700", bgColor: "" },
    { id: "sent", name: names.sent, icon: Send, color: "text-gray-700", bgColor: "" },
    { id: "drafts", name: names.drafts, icon: FileText, color: "text-gray-700", bgColor: "" },
    { id: "important", name: names.important, icon: ImportantIcon as any, color: "text-yellow-700", bgColor: "bg-yellow-100" },
    { id: "all", name: names.all, icon: Users, color: "text-gray-700", bgColor: "" },
    { id: "spam", name: names.spam, icon: AlertCircle, color: "text-gray-700", bgColor: "" },
    { id: "trash", name: names.trash, icon: Trash2, color: "text-gray-700", bgColor: "" },
  ]

  // Stabilize SSR by defaulting to built-in order, then syncing from randomization after mount
  const [folderOrder, setFolderOrder] = useState<string[] | null>(null)
  useEffect(() => {
    try {
      const fo = randomization?.sidebarFolderOrder
      setFolderOrder(Array.isArray(fo) ? fo : null)
    } catch {}
  }, [randomization])
  const foldersOrdered = (() => {
    if (!Array.isArray(folderOrder) || folderOrder.length === 0) return folders
    const pos = new Map<string, number>()
    folderOrder.forEach((id: string, idx: number) => pos.set(String(id).toLowerCase(), idx))
    const copy = folders.slice()
    copy.sort((a, b) => {
      const ai = pos.get(String(a.id).toLowerCase())
      const bi = pos.get(String(b.id).toLowerCase())
      if (ai != null && bi != null) return ai - bi
      if (ai != null) return -1
      if (bi != null) return 1
      return 0
    })
    return copy
  })()

  const getEmailCount = (folderId: string) => {
    if (folderUnreadCounts) {
      if (folderId === "all") return folderUnreadCounts["all"] ?? folderUnreadCounts["inbox"] ?? 0
      return folderUnreadCounts[folderId] ?? 0
    }
    // Fallback to local estimation using current list
    if (folderId === "inbox" || folderId === "all") return emails.filter((email) => !email.isRead).length
    if (folderId === "starred") return emails.filter((email) => email.isStarred && !email.isRead).length
    if (folderId === "important") return emails.filter((email) => email.isImportant && !email.isRead).length
    return 0
  }

  const getLabelCount = (labelId: string) => {
    if (labelUnreadCounts) return labelUnreadCounts[labelId] ?? 0
    return emails.filter((email) => !email.isRead && email.labels?.some((label) => label.toLowerCase() === labelId)).length
  }

  if (position === "top") {
    return (
      <div className="w-full border-b border-gray-200 shadow-sm">
        <div className="px-4 py-2 flex items-center gap-3 overflow-x-auto">
          <Button
            className="h-9 bg-blue-500 hover:bg-blue-600 text-white rounded-2xl px-4 shrink-0"
            onClick={onCompose}
          >
            <Plus className="h-4 w-4 mr-2" />
            Compose
          </Button>
          <nav className="flex items-center gap-1">
            {foldersOrdered.map((folder) => {
              const Icon = folder.icon
              const count = getEmailCount(folder.id)
              const isActive = currentFolder === folder.id
              return (
                <Button
                  key={folder.id}
                  variant="ghost"
                  className={`h-9 px-3 shrink-0 ${isActive ? "bg-red-100 text-red-700 font-medium" : "hover:bg-gray-100"}`}
                  onClick={() => onFolderChange(folder.id)}
                  title={folder.name}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  <span className="text-sm">{folder.name}</span>
                  {count > 0 && (
                    <Badge
                      variant="secondary"
                      className={`ml-2 text-2xs ${isActive ? "bg-red-200 text-red-800" : "bg-gray-200 text-gray-700"}`}
                    >
                      {count}
                    </Badge>
                  )}
                </Button>
              )
            })}
          </nav>
          <div className="ml-auto">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-9 px-3">Labels</Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="max-h-72 overflow-auto">
                <DropdownMenuLabel>Select label</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {(() => {
                  const unique = Array.from(new Map((labels || []).map((l) => [l.id, l])).values())
                  return unique
                })().map((label) => {
                  const count = getLabelCount(label.id)
                  const isActive = currentFolder === label.id
                  return (
                    <DropdownMenuItem key={label.id} onClick={() => onFolderChange(label.id)} className={`${isActive ? "bg-red-100 text-red-700" : ""}`}>
                      <span className="flex-1">{label.name}</span>
                      {count > 0 && (
                        <Badge variant="secondary" className="ml-2 text-2xs bg-gray-200 text-gray-700">{count}</Badge>
                      )}
                    </DropdownMenuItem>
                  )
                })}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    )
  }

  return (
    <aside
      className={`${ispsed ? "w-16" : "w-64"} h-full border-r border-gray-200 transition-all duration-200 flex flex-col min-h-0 shadow-sm`}
    >
      {/* Compose Button */}
      <div className="p-4">
        <Button
          className="h-12 bg-blue-500 hover:bg-blue-600 text-white rounded-2xl shadow-md hover:shadow-lg transition-all duration-200 transform hover:scale-105 justify-start"
          onClick={onCompose}
        >
          <Plus className="h-4 w-4 mr-2" />
          {!ispsed && names.compose}
        </Button>
      </div>

      {/* Main Navigation */}
      <nav className="px-2 flex-1 overflow-y-auto">
        <div className="space-y-1">
          {foldersOrdered.map((folder) => {
            const Icon = folder.icon
            const count = getEmailCount(folder.id)
            const isActive = currentFolder === folder.id

            return (
              <Button
                key={folder.id}
                variant="ghost"
                className={`w-full justify-start transition-all duration-200 ${
                  isActive ? "bg-red-100 text-red-700 font-medium shadow-sm" : "hover:bg-gray-100"
                }`}
                onClick={() => onFolderChange(folder.id)}
              >
                <Icon className="h-4 w-4 mr-3 flex-shrink-0" />
                {!ispsed && (
                  <>
                    <span className="flex-1 text-left">{folder.name}</span>
                    {count > 0 && (
                      <Badge
                        variant="secondary"
                        className={`ml-auto text-xs transition-all duration-200 ${
                          isActive ? "bg-red-200 text-red-800" : "bg-gray-200 text-gray-700"
                        }`}
                      >
                        {count}
                      </Badge>
                    )}
                  </>
                )}
              </Button>
            )
          })}
        </div>

        {/* Labels Section */}
        {!ispsed && (
          <div className="mt-6">
            <div className="w-full flex items-center mb-2">
              <Button
                variant="ghost"
                className="flex-1 justify-start text-sm  hover:bg-gray-100 transition-colors"
                onClick={() => setShowLabels(!showLabels)}
              >
                {showLabels ? (
                  <ChevronDown className="h-4 w-4 mr-2 transition-transform duration-200" />
                ) : (
                  <ChevronRight className="h-4 w-4 mr-2 transition-transform duration-200" />
                )}
                Labels
              </Button>
              <Button
                variant="ghost"
                size="icon"
                title="Create label"
                className="ml-1"
                onClick={async () => {
                  try {
                    await onCreateLabel?.()
                    setShowLabels(true)
                  } catch {}
                }}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            <div className={`${showLabels ? "" : "hidden"} max-h-[50vh] overflow-y-auto pr-1`}>
              <div className="space-y-1 ml-2">
                {(() => {
                  const unique = Array.from(new Map((labels || []).map((l) => [l.id, l])).values())
                  return unique
                })().map((label) => {
                  const count = getLabelCount(label.id)
                  const isActive = currentFolder === label.id
                  const isHex = typeof label.color === "string" && label.color.trim().startsWith("#")

                  return (
                    <Button
                      key={label.id}
                      variant="ghost"
                      className={`w-full justify-start text-sm transition-all duration-200 ${
                        isActive ? "bg-red-100 text-red-700 font-medium" : "hover:bg-gray-100"
                      }`}
                      onClick={() => onFolderChange(label.id)}
                    >
                      <Tag className="h-3 w-3 mr-3 flex-shrink-0" />
                      <div
                        className={`w-2 h-2 rounded-full mr-2 shadow-sm ${!isHex && label.color ? label.color : ""}`}
                        style={isHex ? { backgroundColor: label.color as string } : undefined}
                      ></div>
                      <span className="flex-1 text-left injectable">{label.name}</span>
                      {count > 0 && (
                        <Badge
                          variant="secondary"
                          className={`ml-auto text-xs ${isActive ? "bg-red-200 text-red-800" : "bg-gray-200 text-gray-700"}`}
                        >
                          {count}
                        </Badge>
                      )}
                    </Button>
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </nav>
    </aside>
  )
}
