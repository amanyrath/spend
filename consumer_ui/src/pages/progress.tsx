import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { RetroBadge } from "@/components/ui/retro-badge"
import { getValidUserId } from "@/lib/utils"

interface CompletedMission {
  id: string
  title: string
  completedDate: string
  impact: string
}

export function ProgressPage() {
  const { userId } = useParams<{ userId: string }>()
  const [loading, setLoading] = useState(true)
  const [completedMissions, setCompletedMissions] = useState<CompletedMission[]>([])

  useEffect(() => {
    if (!userId) {
      setLoading(false)
      return
    }

    const validUserId = getValidUserId(userId)
    // TODO: Fetch progress data from API
    setCompletedMissions([
      {
        id: "1",
        title: "Build $1,000 Emergency Fund",
        completedDate: "3 months ago",
        impact: "$1,000 saved"
      },
      {
        id: "2",
        title: "Audit Subscriptions",
        completedDate: "1 month ago",
        impact: "$64/month freed"
      }
    ])
    setLoading(false)
  }, [userId])

  if (loading) {
    return (
      <div>
        <div className="text-center font-mono">Loading progress...</div>
      </div>
    )
  }

  return (
    <div>
      {/* Active Mission */}
      <RetroCard className="mb-5">
        <RetroCardHeader>
          <RetroCardTitle className="text-base">ACTIVE MISSION</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <div className="space-y-3">
            <div className="font-mono text-sm">💳 Get Credit Usage Below 30%</div>
            <div className="text-xs font-mono text-retro-charcoal-light">
              Started: 2 weeks ago | Target: 3 months
            </div>
          </div>
        </RetroCardContent>
      </RetroCard>

      {/* Completed Missions */}
      <RetroCard className="mb-5">
        <RetroCardHeader>
          <RetroCardTitle className="text-base">COMPLETED MISSIONS</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <div className="space-y-4">
            {completedMissions.map((mission) => (
              <div key={mission.id} className="border-b border-retro-border last:border-0 pb-4 last:pb-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-trust-success font-mono">✓</span>
                      <span className="font-mono text-sm font-semibold">{mission.title}</span>
                    </div>
                    <div className="text-xs font-mono text-retro-charcoal-light ml-6">
                      Completed: {mission.completedDate}
                    </div>
                    <div className="text-xs font-mono text-retro-charcoal-light ml-6">
                      Impact: {mission.impact}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </RetroCardContent>
      </RetroCard>

      {/* Total Impact */}
      <RetroCard>
        <RetroCardHeader>
          <RetroCardTitle className="text-base">TOTAL IMPACT SO FAR</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center">
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                Monthly Savings
              </div>
              <div className="text-2xl font-mono font-bold text-retro-charcoal">$151</div>
            </div>
            <div className="text-center">
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                Missions Complete
              </div>
              <div className="text-2xl font-mono font-bold text-retro-charcoal">
                {completedMissions.length}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs font-mono text-retro-charcoal-light uppercase tracking-wider mb-1">
                Financial Health
              </div>
              <RetroBadge variant="success" size="lg">Improving</RetroBadge>
            </div>
          </div>
        </RetroCardContent>
      </RetroCard>
    </div>
  )
}


