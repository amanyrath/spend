import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { MissionCard } from "@/components/mission-card"
import { PowerMoveCard } from "@/components/power-move-card"
import { FinancialSnapshot } from "@/components/financial-snapshot"
import { RecentActivity } from "@/components/recent-activity"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { getValidUserId } from "@/lib/utils"
import { fetchMissionData, fetchTransactions, type MissionData, type Transaction } from "@/lib/api"

export function MissionPage() {
  const { userId } = useParams<{ userId: string }>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [missionData, setMissionData] = useState<MissionData | null>(null)
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([])

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
        <div className="text-center font-mono">Loading mission...</div>
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

      {/* Recent Activity */}
      <div className="mb-5">
        <RecentActivity transactions={recentTransactions} />
      </div>
    </div>
  )
}


