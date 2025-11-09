import * as React from "react"
import { cn } from "@/lib/utils"

export interface RetroLoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg"
  text?: string
}

const RetroLoader = React.forwardRef<HTMLDivElement, RetroLoaderProps>(
  ({ className, size = "md", text = "Loading...", ...props }, ref) => {
    const sizeClasses = {
      sm: "h-4 w-4 text-xs",
      md: "h-6 w-6 text-sm",
      lg: "h-8 w-8 text-base",
    }
    
    return (
      <div
        ref={ref}
        className={cn("flex items-center gap-2 font-mono", className)}
        {...props}
      >
        <div
          className={cn(
            "border-2 border-retro-border border-t-trust-primary rounded-full animate-spin",
            sizeClasses[size]
          )}
        />
        {text && (
          <span className={cn("text-retro-charcoal-light", sizeClasses[size])}>
            {text}
          </span>
        )}
      </div>
    )
  }
)
RetroLoader.displayName = "RetroLoader"

export { RetroLoader }








