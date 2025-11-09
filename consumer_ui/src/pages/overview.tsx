import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { RetroCard, RetroCardContent, RetroCardHeader, RetroCardTitle } from "@/components/ui/retro-card"
import { RetroBadge } from "@/components/ui/retro-badge"
import { fetchOverview, type OverviewData, type Account } from "@/lib/api"
import { Wallet, TrendingUp, CreditCard } from "lucide-react"
import { getValidUserId, formatCurrency, formatPercentage } from "@/lib/utils"

// Health status badge component
function HealthBadge({ status }: { status: "good" | "fair" | "needs_attention" }) {
  const variants = {
    good: "success" as const,
    fair: "warning" as const,
    needs_attention: "destructive" as const,
  }

  const labels = {
    good: "Good",
    fair: "Fair",
    needs_attention: "Needs Attention",
  }

  return (
    <RetroBadge variant={variants[status]}>
      {labels[status]}
    </RetroBadge>
  )
}

// Account card component
function AccountCard({ account }: { account: Account }) {
  return (
    <RetroCard>
      <RetroCardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="text-sm font-mono text-retro-charcoal-light mb-1">****{account.mask}</div>
            <div className="text-sm font-mono font-medium text-retro-charcoal mb-2">{account.name}</div>
            <div className="text-2xl font-mono font-bold text-retro-charcoal tabular-nums">{formatCurrency(account.balance)}</div>
          </div>
          {account.utilization !== undefined && (
            <div className="text-right">
              <div className="text-xs font-mono text-retro-charcoal-light mb-1 uppercase tracking-wider">Utilization</div>
              <div
                className={`text-sm font-mono font-semibold ${
                  account.utilization >= 80
                    ? "text-trust-error"
                    : account.utilization >= 50
                    ? "text-trust-warning"
                    : "text-trust-success"
                }`}
              >
                {formatPercentage(account.utilization)}
              </div>
              {account.limit && (
                <div className="text-xs font-mono text-retro-charcoal-light mt-1">
                  {formatCurrency(account.available || 0)} available
                </div>
              )}
            </div>
          )}
        </div>
        {account.limit && (
          <div className="mt-3 pt-3 border-t border-retro-border">
            <div className="flex justify-between text-xs font-mono text-retro-charcoal-light">
              <span>Credit Limit</span>
              <span className="tabular-nums">{formatCurrency(account.limit)}</span>
            </div>
          </div>
        )}
      </RetroCardContent>
    </RetroCard>
  )
}

// Account section component
function AccountSection({
  title,
  accounts,
  icon: Icon,
}: {
  title: string
  accounts: Account[]
  icon: React.ElementType
}) {
  if (accounts.length === 0) return null

  return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-retro-charcoal-light" />
          <h2 className="text-lg font-mono font-semibold text-retro-charcoal">{title}</h2>
        </div>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {accounts.map((account) => (
          <AccountCard key={account.account_id} account={account} />
        ))}
      </div>
    </div>
  )
}

export function OverviewPage() {
  const { userId } = useParams<{ userId: string }>()
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!userId) {
      setError("User ID is required")
      setLoading(false)
      return
    }

    const validUserId = getValidUserId(userId)
    setLoading(true)
    fetchOverview(validUserId)
      .then((data) => {
        setOverview(data)
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
        <div className="text-center">Loading overview...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <RetroCard className="border-destructive">
          <RetroCardContent className="pt-6">
            <p className="text-destructive">Error: {error}</p>
          </RetroCardContent>
        </RetroCard>
      </div>
    )
  }

  if (!overview) {
    return (
      <div>
        <RetroCard>
          <RetroCardContent className="pt-6">
            <p className="text-muted-foreground text-center">No overview data available.</p>
          </RetroCardContent>
        </RetroCard>
      </div>
    )
  }

  const { summary, accounts, health } = overview.data

  return (
    <div>
      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-5">
        <RetroCard>
          <RetroCardHeader className="pb-3">
            <RetroCardTitle className="text-xs font-medium font-mono text-retro-charcoal-light uppercase tracking-wider">
              Net Worth
            </RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="text-3xl font-bold font-mono text-retro-charcoal tabular-nums">{formatCurrency(summary.net_worth)}</div>
          </RetroCardContent>
        </RetroCard>

        <RetroCard>
          <RetroCardHeader className="pb-3">
            <RetroCardTitle className="text-xs font-medium font-mono text-retro-charcoal-light uppercase tracking-wider">
              Total Savings
            </RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="text-3xl font-bold font-mono text-retro-charcoal tabular-nums">{formatCurrency(summary.total_savings)}</div>
          </RetroCardContent>
        </RetroCard>

        <RetroCard>
          <RetroCardHeader className="pb-3">
            <RetroCardTitle className="text-xs font-medium font-mono text-retro-charcoal-light uppercase tracking-wider">
              Credit Debt
            </RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="text-3xl font-bold font-mono text-retro-charcoal tabular-nums">{formatCurrency(summary.total_credit_debt)}</div>
          </RetroCardContent>
        </RetroCard>

        <RetroCard>
          <RetroCardHeader className="pb-3">
            <RetroCardTitle className="text-xs font-medium font-mono text-retro-charcoal-light uppercase tracking-wider">
              Available Credit
            </RetroCardTitle>
          </RetroCardHeader>
          <RetroCardContent>
            <div className="text-3xl font-bold font-mono text-retro-charcoal tabular-nums">{formatCurrency(summary.available_credit)}</div>
          </RetroCardContent>
        </RetroCard>
      </div>

      {/* Accounts Sections */}
      <div className="space-y-8 mb-5">
        <AccountSection
          title="Checking Accounts"
          accounts={accounts.checking}
          icon={Wallet}
        />

        <AccountSection
          title="Savings Accounts"
          accounts={accounts.savings}
          icon={TrendingUp}
        />

        <AccountSection
          title="Credit Cards"
          accounts={accounts.credit}
          icon={CreditCard}
        />
      </div>

      {/* Financial Health Summary */}
      <RetroCard>
        <RetroCardHeader className="pb-4">
          <RetroCardTitle className="text-xl font-mono">Financial Health</RetroCardTitle>
        </RetroCardHeader>
        <RetroCardContent>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <div className="text-sm font-mono text-retro-charcoal-light mb-2 uppercase tracking-wider">Overall Status</div>
              <HealthBadge status={health.overall} />
            </div>

            <div>
              <div className="text-sm font-mono text-retro-charcoal-light mb-2 uppercase tracking-wider">Credit Utilization</div>
              <div
                className={`text-lg font-mono font-semibold tabular-nums ${
                  health.credit_utilization >= 80
                    ? "text-trust-error"
                    : health.credit_utilization >= 50
                    ? "text-trust-warning"
                    : "text-trust-success"
                }`}
              >
                {formatPercentage(health.credit_utilization)}
              </div>
            </div>

            {health.emergency_fund_months !== null && (
              <div>
                <div className="text-sm font-mono text-retro-charcoal-light mb-2 uppercase tracking-wider">Emergency Fund</div>
                <div className="text-lg font-mono font-semibold text-retro-charcoal tabular-nums">
                  {health.emergency_fund_months.toFixed(1)} months
                </div>
              </div>
            )}

            <div>
              <div className="text-sm font-mono text-retro-charcoal-light mb-2 uppercase tracking-wider">Cash Flow</div>
              <div
                className={`text-lg font-mono font-semibold ${
                  health.cash_flow_status === "negative"
                    ? "text-trust-error"
                    : health.cash_flow_status === "tight"
                    ? "text-trust-warning"
                    : "text-trust-success"
                }`}
              >
                {health.cash_flow_status === "positive"
                  ? "Positive"
                  : health.cash_flow_status === "tight"
                  ? "Tight"
                  : "Negative"}
              </div>
            </div>
          </div>
        </RetroCardContent>
      </RetroCard>
    </div>
  )
}

