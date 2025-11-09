import * as React from "react"
import { cn } from "@/lib/utils"

export interface ChatIconProps {
  onClick?: () => void
  className?: string
  hasUnread?: boolean
}

export function ChatIcon({ onClick, className, hasUnread = false }: ChatIconProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-10 h-10",
        "bg-white border-2 border-retro-charcoal",
        "flex items-center justify-center",
        "font-mono text-lg font-bold text-retro-charcoal",
        "hover:bg-retro-charcoal hover:text-white",
        "transition-all duration-200",
        "shadow-sm hover:shadow-md",
        "focus:outline-none focus:ring-2 focus:ring-trust-primary focus:ring-offset-2",
        className
      )}
      aria-label="Open chat"
      title="Ask a question"
    >
      <span className="relative">
        ?
        {hasUnread && (
          <span
            className="absolute -top-1 -right-1 w-2 h-2 bg-trust-primary rounded-full border border-white"
            aria-label="Unread messages"
          />
        )}
      </span>
    </button>
  )
}

