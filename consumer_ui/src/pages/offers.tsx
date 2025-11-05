import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { OfferCard } from "@/components/offer-card"
import { fetchRecommendations } from "@/lib/api"
import type { Recommendation } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { getValidUserId } from "@/lib/utils"

export function OffersPage() {
  const { userId } = useParams<{ userId: string }>()
  const [offers, setOffers] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!userId) {
      setError("User ID is required")
      setLoading(false)
      return
    }
    
    const validUserId = getValidUserId(userId)
    fetchRecommendations(validUserId)
      .then((response) => {
        // Use offers from new response format
        setOffers(response.data.offers)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [userId])

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading offers...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">Error: {error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (offers.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            No partner offers available at this time.
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Partner Offers</h1>
        <p className="text-muted-foreground">
          Personalized offers based on your financial profile
        </p>
      </div>
      <div className="space-y-6">
        {offers.map((offer) => (
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
  )
}

