import * as React from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { RationaleBox } from "@/components/rationale-box"
import { Badge } from "@/components/ui/badge"
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
    <Card className={cn("w-full", className)}>
      <CardHeader>
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
                <CardTitle className="text-xl mb-1">{title}</CardTitle>
                <CardDescription className="text-sm text-muted-foreground">
                  {partner}
                </CardDescription>
              </div>
              <Badge
                className={cn(
                  "flex items-center gap-1",
                  isEligible
                    ? "bg-green-100 text-green-800 border-green-200"
                    : "bg-yellow-100 text-yellow-800 border-yellow-200"
                )}
              >
                {isEligible ? (
                  <>
                    <CheckCircle2 className="h-3 w-3" />
                    You may be eligible
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3" />
                    Requirements not met
                  </>
                )}
              </Badge>
            </div>
            <CardDescription className="text-base mt-2">{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <RationaleBox rationale={rationale} />
        {!isEligible && (
          <div className="text-sm text-muted-foreground bg-yellow-50 border border-yellow-200 rounded-md p-3">
            This offer may require specific eligibility criteria that are not currently met. Check with the partner for details.
          </div>
        )}
      </CardContent>
      <CardFooter className="flex flex-col gap-3">
        <Button
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
        </Button>
        <p className="text-xs text-muted-foreground text-center">
          SpendSense may receive compensation. This is not a recommendation.
        </p>
      </CardFooter>
    </Card>
  )
}

