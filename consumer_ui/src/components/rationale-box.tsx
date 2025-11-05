import * as React from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface RationaleBoxProps {
  rationale: string
  className?: string
  expandable?: boolean
}

export function RationaleBox({ rationale, className, expandable = false }: RationaleBoxProps) {
  const [expanded, setExpanded] = React.useState(!expandable)

  return (
    <div
      className={cn(
        "bg-[var(--color-rationale-bg)] border-l-4 border-[var(--color-primary)] p-4 rounded-md",
        className
      )}
      role="region"
      aria-label="Rationale for recommendation"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="text-xs font-semibold text-[var(--color-primary)] uppercase tracking-wide mb-2">
            Why we're showing this
          </div>
          <div
            className={cn(
              "text-sm text-foreground leading-relaxed",
              !expanded && expandable && "line-clamp-2"
            )}
          >
            {rationale}
          </div>
        </div>
        {expandable && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex-shrink-0 p-1 hover:bg-white/50 rounded transition-colors"
            aria-label={expanded ? "Collapse rationale" : "Expand rationale"}
            aria-expanded={expanded}
          >
            <ChevronDown
              className={cn(
                "h-4 w-4 text-[var(--color-primary)] transition-transform",
                expanded && "rotate-180"
              )}
            />
          </button>
        )}
      </div>
    </div>
  )
}

