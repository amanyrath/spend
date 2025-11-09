import * as React from "react"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { RetroButton } from "@/components/ui/retro-button"
import { cn } from "@/lib/utils"

export interface PowerMoveCardProps {
  title: string
  description: string
  timeline?: string
  impact?: string
  difficulty?: string
  risk?: string
  onClick?: () => void
  className?: string
}

export function PowerMoveCard({
  title,
  description,
  timeline,
  impact,
  difficulty,
  risk,
  onClick,
  className
}: PowerMoveCardProps) {
  return (
    <RetroCard 
      className={cn(
        "hover:border-retro-gold hover:shadow-lg transition-all",
        className
      )}
    >
      <RetroCardHeader className="pb-3">
        <RetroCardTitle className="text-sm font-semibold">{title}</RetroCardTitle>
      </RetroCardHeader>
      <RetroCardContent className="space-y-3 pt-0">
        <p className="text-xs font-mono text-retro-charcoal-light leading-relaxed mb-3">
          {description}
        </p>
        
        {(timeline || impact) && (
          <div className="text-[11px] font-mono text-retro-charcoal-light space-y-1 mb-3">
            {timeline && <span className="inline-block mr-3">Timeline: {timeline}</span>}
            {impact && <span className="inline-block">Impact: {impact}</span>}
          </div>
        )}
        
        <RetroButton 
          variant="default" 
          size="sm" 
          className="w-full uppercase tracking-wider text-xs font-semibold"
          onClick={(e) => {
            e.stopPropagation()
            onClick?.()
          }}
        >
          REVIEW
        </RetroButton>
      </RetroCardContent>
    </RetroCard>
  )
}


