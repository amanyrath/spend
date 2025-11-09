import { useEffect, useState, useRef } from "react"
import { useParams } from "react-router-dom"
import { OfferCard } from "@/components/offer-card"
import { CreditOfferCard } from "@/components/credit-offer-card"
import { fetchRecommendations, fetchCreditOffers } from "@/lib/api"
import type { Recommendation, ProductOffer } from "@/lib/api"
import { RetroCard, RetroCardContent } from "@/components/ui/retro-card"
import { RetroBadge } from "@/components/ui/retro-badge"
import { getValidUserId } from "@/lib/utils"

export function OffersPage() {
  const { userId } = useParams<{ userId: string }>()
  const [partnerOffers, setPartnerOffers] = useState<Recommendation[]>([])
  const [creditOffers, setCreditOffers] = useState<ProductOffer[]>([])
  const [creditRating, setCreditRating] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const isMountedRef = useRef(true)

  useEffect(() => {
    if (!userId) {
      setError("User ID is required")
      setLoading(false)
      return
    }
    
    isMountedRef.current = true
    const validUserId = getValidUserId(userId)
    console.log("[OffersPage] Starting fetch for userId:", validUserId)
    console.log("[OffersPage] API_BASE_URL:", import.meta.env.VITE_API_URL || 'http://localhost:8000')
    
    // Add timeout check
    const startTime = Date.now()
    
    // Fetch both partner offers and credit offers
    Promise.all([
      fetchRecommendations(validUserId)
        .then((response) => {
          console.log("[OffersPage] Partner offers response:", response)
          return response
        })
        .catch((err) => {
          console.error("[OffersPage] Failed to fetch partner offers:", err)
          console.error("[OffersPage] Partner offers error details:", {
            message: err.message,
            stack: err.stack,
            name: err.name
          })
          return { data: { offers: [] } }
        }),
      fetchCreditOffers(validUserId)
        .then((response) => {
          console.log("[OffersPage] Credit offers response:", response)
          console.log("[OffersPage] Credit offers count:", response?.qualifiedProducts?.length || 0)
          return response
        })
        .catch((err) => {
          console.error("[OffersPage] Failed to fetch credit offers:", err)
          console.error("[OffersPage] Credit offers error details:", {
            message: err.message,
            stack: err.stack,
            name: err.name,
            response: err.response
          })
          return null
        })
    ])
      .then(([recommendationsResponse, creditOffersResponse]) => {
        if (!isMountedRef.current) return
        
        const elapsed = Date.now() - startTime
        console.log(`[OffersPage] Fetch completed in ${elapsed}ms`)
        
        // Set partner offers
        const partnerOffersList = recommendationsResponse?.data?.offers || []
        console.log("[OffersPage] Setting partner offers:", partnerOffersList.length)
        setPartnerOffers(partnerOffersList)
        
        // Set credit offers (sorted by match percentage)
        if (creditOffersResponse) {
          const sortedOffers = [...creditOffersResponse.qualifiedProducts].sort(
            (a, b) => b.matchPercentage - a.matchPercentage
          )
          console.log("[OffersPage] Setting credit offers:", sortedOffers.length)
          setCreditOffers(sortedOffers)
          setCreditRating(creditOffersResponse.customerCreditRating)
        } else {
          console.log("[OffersPage] No credit offers received")
        }
        
        setLoading(false)
      })
      .catch((err) => {
        if (!isMountedRef.current) return
        
        const elapsed = Date.now() - startTime
        console.error(`[OffersPage] Promise.all failed after ${elapsed}ms:`, err)
        console.error("[OffersPage] Error details:", {
          message: err.message,
          stack: err.stack,
          name: err.name
        })
        setError(err.message || "Failed to load offers")
        setLoading(false)
      })
    
    // Timeout check - if still loading after 15 seconds, show error
    const timeoutId = setTimeout(() => {
      if (isMountedRef.current) {
        console.error("[OffersPage] Request timeout after 15 seconds")
        setError("Request timed out. Check browser console and network tab for details.")
        setLoading(false)
      }
    }, 15000)
    
    return () => {
      isMountedRef.current = false
      clearTimeout(timeoutId)
    }
  }, [userId])

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center font-mono">Loading offers...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <RetroCard className="border-trust-error">
          <RetroCardContent className="pt-6">
            <p className="text-trust-error font-mono">Error: {error}</p>
          </RetroCardContent>
        </RetroCard>
      </div>
    )
  }

  const hasCreditOffers = creditOffers.length > 0
  const hasPartnerOffers = partnerOffers.length > 0
  const hasAnyOffers = hasCreditOffers || hasPartnerOffers

  if (!hasAnyOffers) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <RetroCard>
          <RetroCardContent className="pt-6 text-center text-retro-charcoal-light font-mono">
            No offers available at this time.
          </RetroCardContent>
        </RetroCard>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold font-mono mb-2 text-retro-charcoal tracking-wide">
          CREDIT OFFERS
        </h1>
        <p className="text-retro-charcoal-light font-mono text-sm uppercase tracking-wider">
          Personalized credit card offers based on your financial profile
        </p>
        {creditRating && (
          <div className="mt-4">
            <RetroBadge variant="outline" className="text-xs">
              Your Credit Rating: {creditRating}
            </RetroBadge>
          </div>
        )}
      </div>

      {/* Credit Offers Section */}
      {hasCreditOffers && (
        <div className="mb-12">
          <h2 className="text-xl font-bold font-mono mb-4 text-retro-charcoal tracking-wide uppercase">
            Pre-Qualified Credit Cards
          </h2>
          <p className="text-sm font-mono text-retro-charcoal-light mb-6 uppercase tracking-wider">
            Offers matched to your financial profile ({creditOffers.length} available)
          </p>
          <div className="space-y-6">
            {creditOffers.map((offer) => (
              <CreditOfferCard key={offer.productId} offer={offer} />
            ))}
          </div>
        </div>
      )}

      {/* Partner Offers Section */}
      {hasPartnerOffers && (
        <div className={hasCreditOffers ? "border-t border-retro-border pt-12" : ""}>
          <h2 className="text-xl font-bold font-mono mb-4 text-retro-charcoal tracking-wide uppercase">
            Partner Offers
          </h2>
          <p className="text-sm font-mono text-retro-charcoal-light mb-6 uppercase tracking-wider">
            Additional offers from our partners
          </p>
          <div className="space-y-6">
            {partnerOffers.map((offer) => (
              <OfferCard
                key={offer.recommendation_id}
                title={offer.title}
                description={offer.description || offer.rationale.split(".")[0] + "."}
                rationale={offer.rationale}
                contentId={offer.content_id}
                partner={offer.partner}
                partner_logo_url={offer.partner_logo_url}
                eligibility={offer.eligibility}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

