import * as React from "react"
import { RetroCard, RetroCardContent, RetroCardDescription, RetroCardFooter, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { RetroButton } from "@/components/ui/retro-button"
import { RationaleBox } from "@/components/rationale-box"
import { RetroBadge } from "@/components/ui/retro-badge"
import { cn } from "@/lib/utils"
import { ExternalLink, CheckCircle2, AlertCircle } from "lucide-react"

interface OfferCardProps {
  title: string
  description: string
  rationale: string
  contentId: string
  partner?: string
  partner_logo_url?: string
  eligibility?: 'eligible' | 'requirements_not_met'
  className?: string
}

export function OfferCard({
  title,
  description,
  rationale,
  contentId: _contentId,
  partner = "Partner",
  partner_logo_url,
  eligibility = "eligible",
  className,
}: OfferCardProps) {
  const isEligible = eligibility === "eligible"

  return (
    <RetroCard className={cn("w-full", className)}>
      <RetroCardHeader>
        <div className="flex items-start gap-4">
          {partner_logo_url && (
            <div className="flex-shrink-0">
              <img
                src={partner_logo_url}
                alt={partner}
                className="h-12 w-12 object-contain rounded"
                onError={(e) => {
                  // Hide image if it fails to load
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
          )}
          <div className="flex-1">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex-1">
                <RetroCardTitle className="text-lg font-mono mb-1">{title}</RetroCardTitle>
                <RetroCardDescription className="text-xs font-mono">
                  {partner}
                </RetroCardDescription>
              </div>
              <RetroBadge
                variant={isEligible ? "success" : "warning"}
                className="flex items-center gap-1"
              >
                {isEligible ? (
                  <>
                    <CheckCircle2 className="h-3 w-3" />
                    Eligible
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3" />
                    Requirements not met
                  </>
                )}
              </RetroBadge>
            </div>
            <RetroCardDescription className="text-sm font-mono mt-2 normal-case">{description}</RetroCardDescription>
          </div>
        </div>
      </RetroCardHeader>
      <RetroCardContent className="space-y-4">
        <RationaleBox rationale={rationale} />
        {!isEligible && (
          <div className="text-sm font-mono text-retro-charcoal-light bg-yellow-50 border border-yellow-200 p-3">
            This offer may require specific eligibility criteria that are not currently met. Check with the partner for details.
          </div>
        )}
      </RetroCardContent>
      <RetroCardFooter className="flex flex-col gap-3">
        <RetroButton
          variant="default"
          className="w-full"
          onClick={() => {
            // In a real implementation, this would navigate to partner offer page
            // For now, we'll just open a placeholder
            window.open(`#offer-${_contentId}`, '_blank')
          }}
        >
          Learn More
          <ExternalLink className="ml-2 h-4 w-4" />
        </RetroButton>
        <p className="text-xs font-mono text-retro-charcoal-light text-center">
          SpendSense may receive compensation. This is not a recommendation.
        </p>
      </RetroCardFooter>
    </RetroCard>
  )
}




