import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { EducationCard } from "@/components/education-card"
import { PersonaModuleRouter } from "@/components/education/PersonaModuleRouter"
import { fetchRecommendations } from "@/lib/api"
import type { Recommendation } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { getValidUserId } from "@/lib/utils"

export function EducationPage() {
  const { userId } = useParams<{ userId: string }>()
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!userId) {
      setError("User ID is required")
      setLoading(false)
      return
    }
    
    const validUserId = getValidUserId(userId)
    
    // Load recommendations
    fetchRecommendations(validUserId)
      .then((response) => {
        setRecommendations(response.data.education)
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
        <div className="text-center">Loading education content...</div>
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

  const validUserId = userId ? getValidUserId(userId) : ""

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Financial Education</h1>
        <p className="text-muted-foreground">
          Personalized financial guidance based on your account activity
        </p>
      </div>
      
      {/* Interactive Persona Module */}
      {validUserId && (
        <div className="mb-8">
          <PersonaModuleRouter 
            userId={validUserId} 
            key={validUserId}
          />
        </div>
      )}

      {/* Static Education Cards (fallback or additional content) */}
      {recommendations.length > 0 && (
        <div className="space-y-6">
          {recommendations.map((rec) => (
            <EducationCard
              key={rec.recommendation_id}
              title={rec.title}
              description={rec.description || rec.rationale.split(".")[0] + "."}
              rationale={rec.rationale}
              contentId={rec.content_id}
              category={rec.category || "general"}
              fullContent={rec.full_content || rec.rationale}
              tags={rec.tags}
            />
          ))}
        </div>
      )}

      {recommendations.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            No education content available at this time.
          </CardContent>
        </Card>
      )}

      <div className="mt-8 pt-6 border-t">
        <p className="text-sm text-muted-foreground text-center">
          This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.
        </p>
      </div>
    </div>
  )
}

