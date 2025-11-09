import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { MissionCard } from "@/components/mission-card"
import { PowerMoveCard } from "@/components/power-move-card"
import { FinancialSnapshot } from "@/components/financial-snapshot"
import { RecentActivity } from "@/components/recent-activity"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { RetroBadge } from "@/components/ui/retro-badge"
import { getValidUserId } from "@/lib/utils"
import { fetchMissionData, fetchTransactions, type MissionData, type Transaction } from "@/lib/api"

interface CompletedMission {
  id: string
  title: string
  completedDate: string
  impact: string
}

export function DashboardPage() {
  const { userId } = useParams<{ userId: string }>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [missionData, setMissionData] = useState<MissionData | null>(null)
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([])
  const [completedMissions, setCompletedMissions] = useState<CompletedMission[]>([])

  useEffect(() => {
    if (!userId) {
      setLoading(false)
      return
    }

    const validUserId = getValidUserId(userId)
    setLoading(true)
    setError(null)

    Promise.all([
      fetchMissionData(validUserId),
      fetchTransactions(validUserId, undefined, 20) // Get last 20 transactions
    ])
      .then(([data, transactions]) => {
        setMissionData(data)
        setRecentTransactions(transactions)
        // TODO: Fetch actual progress data from API
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
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [userId])

  if (loading) {
    return (
      <div>
        <div className="text-center font-mono">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="text-center font-mono text-destructive">Error: {error}</div>
      </div>
    )
  }

  if (!missionData) {
    return (
      <div>
        <div className="text-center font-mono">No mission data available.</div>
      </div>
    )
  }

  return (
    <div>
      {/* Active Mission */}
      <div className="mb-5">
        <MissionCard
          title={missionData.mission.title}
          subtitle={missionData.mission.subtitle}
          currentValue={missionData.mission.currentValue}
          targetValue={missionData.mission.targetValue}
          unit={missionData.mission.unit}
          amountAway={missionData.mission.amountAway}
          estimatedMonths={missionData.mission.estimatedMonths}
        />
      </div>

      {/* Power Moves */}
      <div className="mb-5">
        <RetroCard>
          <RetroCardHeader>
            <RetroCardTitle className="text-base">⚡ NEXT STEPS</RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {missionData.powerMoves.map((move, index) => (
                <PowerMoveCard
                  key={index}
                  title={move.title}
                  description={move.description}
                  timeline={move.timeline}
                  impact={move.impact}
                  risk={move.risk}
                  onClick={() => console.log(`Review: ${move.title}`)}
                />
              ))}
            </div>
          </RetroCardContent>
        </RetroCard>
      </div>

      {/* Financial Snapshot */}
      <div className="mb-5">
        <FinancialSnapshot
          netWorth={missionData.financialSnapshot.netWorth}
          totalSavings={missionData.financialSnapshot.totalSavings}
          creditDebt={missionData.financialSnapshot.creditDebt}
          availableCredit={missionData.financialSnapshot.availableCredit}
        />
      </div>

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
      <RetroCard className="mb-5">
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

      {/* Recent Activity */}
      <div className="mb-5">
        <RecentActivity transactions={recentTransactions} />
      </div>
    </div>
  )
}





