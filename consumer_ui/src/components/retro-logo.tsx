import * as React from "react"
import { cn } from "@/lib/utils"

export interface RetroLogoProps {
  className?: string
  size?: "sm" | "md" | "lg"
}

export function RetroLogo({ className, size = "md" }: RetroLogoProps) {
  const sizeClasses = {
    sm: "text-lg",
    md: "text-2xl",
    lg: "text-4xl",
  }
  
  // ASCII art logo from spendsense_ascii_context.md
  const asciiLogo = `███████╗██████╗ ███████╗███╗   ██╗██████╗ ███████╗███████╗███╗   ██╗███████╗███████╗
██╔════╝██╔══██╗██╔════╝████╗  ██║██╔══██╗██╔════╝██╔════╝████╗  ██║██╔════╝██╔════╝
███████╗██████╔╝█████╗  ██╔██╗ ██║██║  ██║█████╗  ███████╗██╔██╗ ██║███████╗█████╗  
╚════██║██╔══██╗██╔══╝  ██║╚██╗██║██║  ██║██╔══╝  ╚════██║██║╚██╗██║╚════██║██╔══╝  
███████║██║  ██║███████╗██║ ╚████║██████╔╝███████╗███████║██║ ╚████║███████║███████╗
╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚══════╝`

  return (
    <div className={cn("font-mono", className)}>
      <div className={cn("font-bold text-trust-primary tracking-wider", sizeClasses[size])}>
        SPENDSENSE
      </div>
      <div className="text-xs text-retro-charcoal-light font-mono mt-1">
        One mission at a time. Clear progress. Real results.
      </div>
    </div>
  )
}








