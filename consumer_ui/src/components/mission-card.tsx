import * as React from "react"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle, RetroCardDescription } from "@/components/ui/retro-card"
import { cn } from "@/lib/utils"

export interface MissionCardProps {
  title: string
  subtitle?: string
  currentValue: number
  targetValue: number
  unit?: string
  amountAway?: number
  estimatedMonths?: number
  className?: string
}

export function MissionCard({ 
  title, 
  subtitle, 
  currentValue, 
  targetValue, 
  unit = "%",
  amountAway,
  estimatedMonths,
  className 
}: MissionCardProps) {
  // For credit utilization, show current percentage
  // For other missions, calculate progress differently
  const displayValue = unit === "%" ? currentValue : currentValue
  const displayMax = unit === "%" ? 100 : targetValue
  
  // Calculate percentage for progress bar (for credit utilization, show current %)
  const progressPercentage = unit === "%" ? currentValue : Math.min(100, (currentValue / targetValue) * 100)
  
  return (
    <RetroCard variant="gold-accent" className={cn("bg-yellow-50", className)}>
      <RetroCardHeader>
        <RetroCardTitle className="text-lg font-bold">{title}</RetroCardTitle>
        {subtitle && <RetroCardDescription>{subtitle}</RetroCardDescription>}
      </RetroCardHeader>
      <RetroCardContent>
        <div className="space-y-4">
          <div className="flex justify-between text-xs font-mono text-retro-charcoal-light mb-2">
            <span>Current: {currentValue}{unit}</span>
            <span>Target: {targetValue}{unit}</span>
          </div>
          <div className="w-full h-6 bg-gray-200 border border-gray-300 relative overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-trust-primary to-trust-secondary flex items-center justify-end pr-2 transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, progressPercentage))}%` }}
            >
              <span className="text-[11px] font-semibold text-white tracking-wider font-mono">
                {currentValue}{unit}
              </span>
            </div>
          </div>
          <div className="text-xs font-mono text-retro-charcoal-light space-y-1">
            {amountAway !== undefined && amountAway > 0 && (
              <div>You're ${Math.round(amountAway).toLocaleString()} away</div>
            )}
            {estimatedMonths !== undefined && (
              <div>At current pace: {estimatedMonths} {estimatedMonths === 1 ? 'month' : 'months'}</div>
            )}
          </div>
        </div>
      </RetroCardContent>
    </RetroCard>
  )
}

