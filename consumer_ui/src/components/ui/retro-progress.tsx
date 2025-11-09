import * as React from "react"
import { cn } from "@/lib/utils"

export interface RetroProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number
  max?: number
  showLabel?: boolean
  showPercentage?: boolean
  variant?: "default" | "success" | "warning" | "error"
}

const RetroProgress = React.forwardRef<HTMLDivElement, RetroProgressProps>(
  ({ 
    className, 
    value, 
    max = 100, 
    showLabel = true,
    showPercentage = true,
    variant = "default",
    ...props 
  }, ref) => {
    const percentage = Math.round((value / max) * 100)
    const clampedPercentage = Math.min(100, Math.max(0, percentage))
    
    const variantColors = {
      default: "bg-gradient-to-r from-trust-primary to-trust-secondary",
      success: "bg-trust-success",
      warning: "bg-trust-warning",
      error: "bg-trust-error",
    }
    
    return (
      <div ref={ref} className={cn("w-full", className)} {...props}>
        {showLabel && (
          <div className="flex justify-between text-xs font-mono text-retro-charcoal-light mb-2">
            <span>Progress</span>
            {showPercentage && <span className="font-semibold">{percentage}%</span>}
          </div>
        )}
        <div className="w-full h-6 bg-retro-border border border-retro-border overflow-hidden relative">
          <div
            className={cn(
              "h-full flex items-center justify-end pr-2 transition-all duration-300",
              variantColors[variant]
            )}
            style={{ width: `${clampedPercentage}%` }}
          >
            {showPercentage && (
              <span className="text-xs font-mono font-semibold text-white">
                {percentage}%
              </span>
            )}
          </div>
        </div>
      </div>
    )
  }
)
RetroProgress.displayName = "RetroProgress"

export { RetroProgress }








