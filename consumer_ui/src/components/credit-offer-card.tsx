import * as React from "react"
import { RetroCard, RetroCardContent, RetroCardDescription, RetroCardFooter, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { RetroButton } from "@/components/ui/retro-button"
import { RetroBadge } from "@/components/ui/retro-badge"
import { cn } from "@/lib/utils"
import { ExternalLink, TrendingUp, CreditCard, Percent, DollarSign, Award } from "lucide-react"
import type { ProductOffer } from "@/lib/api"

interface CreditOfferCardProps {
  offer: ProductOffer
  className?: string
}

export function CreditOfferCard({ offer, className }: CreditOfferCardProps) {
  const cardImage = offer.images.cardArt?.url || offer.images.cardName?.url
  
  // Determine tier badge variant
  const getTierVariant = (tier: string) => {
    switch (tier.toUpperCase()) {
      case "PREMIUM":
        return "gold" as const
      case "STANDARD":
        return "default" as const
      case "STARTER":
        return "secondary" as const
      case "BANKING":
        return "default" as const
      default:
        return "outline" as const
    }
  }

  // Determine credit rating badge variant
  const getCreditRatingVariant = (rating: string) => {
    switch (rating) {
      case "EXCELLENT":
        return "success" as const
      case "GOOD":
        return "default" as const
      case "FAIR":
        return "warning" as const
      case "POOR":
        return "destructive" as const
      default:
        return "outline" as const
    }
  }

  // Get match percentage color
  const getMatchColor = (percentage: number) => {
    if (percentage >= 90) return "text-trust-success"
    if (percentage >= 75) return "text-trust-primary"
    if (percentage >= 60) return "text-trust-warning"
    return "text-retro-charcoal-light"
  }

  return (
    <RetroCard className={cn("w-full", className)}>
      <RetroCardHeader>
        <div className="flex items-start gap-4">
          {/* Card Image */}
          {cardImage && (
            <div className="flex-shrink-0">
              <img
                src={cardImage}
                alt={offer.images.cardArt?.altText || offer.productDisplayName}
                className="h-32 w-48 object-contain rounded border border-retro-border"
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
          )}
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex-1 min-w-0">
                <RetroCardTitle className="text-lg font-mono mb-2">{offer.productDisplayName}</RetroCardTitle>
                <div className="flex flex-wrap gap-2 mb-2">
                  <RetroBadge variant={getTierVariant(offer.tier)} size="sm">
                    {offer.tier}
                  </RetroBadge>
                  <RetroBadge variant={getCreditRatingVariant(offer.creditRating)} size="sm">
                    {offer.creditRating}
                  </RetroBadge>
                </div>
              </div>
              
              {/* Match Percentage */}
              <div className="flex-shrink-0 text-right">
                <div className={cn("text-3xl font-bold font-mono tabular-nums", getMatchColor(offer.matchPercentage))}>
                  {Math.round(offer.matchPercentage)}%
                </div>
                <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider">
                  Match
                </div>
              </div>
            </div>

            {/* Match Reason */}
            {offer.matchReason && (
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                <p className="text-sm font-mono text-retro-charcoal">{offer.matchReason}</p>
              </div>
            )}
          </div>
        </div>
      </RetroCardHeader>

      <RetroCardContent className="space-y-4">
        {/* Marketing Copy */}
        {offer.mainMarketingCopy && offer.mainMarketingCopy.length > 0 && (
          <div>
            <h4 className="text-xs font-mono font-semibold text-retro-charcoal-light uppercase tracking-wider mb-2">
              Key Benefits
            </h4>
            <ul className="space-y-1">
              {offer.mainMarketingCopy.map((copy, idx) => (
                <li key={idx} className="text-sm font-mono text-retro-charcoal flex items-start gap-2">
                  <span className="text-trust-primary mt-1">•</span>
                  <span>{copy}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* APR Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-retro-border">
          <div>
            <h4 className="text-xs font-mono font-semibold text-retro-charcoal-light uppercase tracking-wider mb-2 flex items-center gap-1">
              <Percent className="h-3 w-3" />
              APR Details
            </h4>
            <div className="space-y-1 text-sm font-mono">
              {offer.introPurchaseApr && (
                <div>
                  <span className="text-retro-charcoal-light">Intro Purchase APR: </span>
                  <span className="text-trust-success font-semibold">{offer.introPurchaseApr}</span>
                </div>
              )}
              <div>
                <span className="text-retro-charcoal-light">Purchase APR: </span>
                <span className="text-retro-charcoal">{offer.purchaseApr}</span>
              </div>
              {offer.introBalanceTransferApr && (
                <div>
                  <span className="text-retro-charcoal-light">Intro Balance Transfer APR: </span>
                  <span className="text-trust-success font-semibold">{offer.introBalanceTransferApr}</span>
                </div>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-mono font-semibold text-retro-charcoal-light uppercase tracking-wider mb-2 flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              Fees
            </h4>
            <div className="space-y-1 text-sm font-mono">
              <div>
                <span className="text-retro-charcoal-light">Annual Fee: </span>
                <span className="text-retro-charcoal">{offer.annualMembershipFee}</span>
              </div>
              {offer.balanceTransferFee && (
                <div>
                  <span className="text-retro-charcoal-light">Balance Transfer Fee: </span>
                  <span className="text-retro-charcoal">{offer.balanceTransferFee}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Estimated Savings */}
        {offer.estimatedSavings && (
          <div className="p-3 bg-green-50 border border-green-200 rounded">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-trust-success" />
              <h4 className="text-xs font-mono font-semibold text-trust-success uppercase tracking-wider">
                Estimated Savings
              </h4>
            </div>
            <p className="text-lg font-mono font-bold text-trust-success">
              {offer.estimatedSavings}
            </p>
          </div>
        )}

        {/* Bonus Information */}
        {offer.bonusAmount && offer.bonusRequirement && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
            <div className="flex items-center gap-2 mb-1">
              <Award className="h-4 w-4 text-trust-warning" />
              <h4 className="text-xs font-mono font-semibold text-trust-warning uppercase tracking-wider">
                Bonus Offer
              </h4>
            </div>
            <p className="text-sm font-mono text-retro-charcoal font-semibold">
              {offer.bonusAmount} bonus
            </p>
            <p className="text-xs font-mono text-retro-charcoal-light mt-1">
              {offer.bonusRequirement}
            </p>
          </div>
        )}

        {/* Extra Marketing Copy */}
        {offer.extraMarketingCopy && offer.extraMarketingCopy.length > 0 && (
          <div className="pt-2 border-t border-retro-border">
            <h4 className="text-xs font-mono font-semibold text-retro-charcoal-light uppercase tracking-wider mb-2">
              Additional Benefits
            </h4>
            <ul className="space-y-1">
              {offer.extraMarketingCopy.map((copy, idx) => (
                <li key={idx} className="text-xs font-mono text-retro-charcoal-light flex items-start gap-2">
                  <span className="text-retro-charcoal-light mt-1">•</span>
                  <span>{copy}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </RetroCardContent>

      <RetroCardFooter className="flex flex-col gap-3">
        <RetroButton
          variant="default"
          className="w-full"
          onClick={() => {
            window.open(offer.applyNowLink, '_blank', 'noopener,noreferrer')
          }}
        >
          Apply Now
          <ExternalLink className="ml-2 h-4 w-4" />
        </RetroButton>
        <p className="text-xs font-mono text-retro-charcoal-light text-center">
          SpendSense may receive compensation. This is not a recommendation.
        </p>
      </RetroCardFooter>
    </RetroCard>
  )
}







