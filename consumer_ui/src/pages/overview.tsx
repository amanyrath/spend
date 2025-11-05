import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchOverview, type OverviewData, type Account } from "@/lib/api"
import { Wallet, TrendingUp, CreditCard } from "lucide-react"
import { getValidUserId, formatCurrency, formatPercentage } from "@/lib/utils"

// Health status badge component
function HealthBadge({ status }: { status: "good" | "fair" | "needs_attention" }) {
  const variants = {
    good: "bg-green-50 text-green-700 border-green-200",
    fair: "bg-yellow-50 text-yellow-700 border-yellow-200",
    needs_attention: "bg-red-50 text-red-700 border-red-200",
  }

  const labels = {
    good: "Good",
    fair: "Fair",
    needs_attention: "Needs Attention",
  }

  return (
    <Badge variant="outline" className={variants[status]}>
      {labels[status]}
    </Badge>
  )
}

// Account card component
function AccountCard({ account }: { account: Account }) {
  return (
    <Card className="border border-gray-200 shadow-sm">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="text-sm text-muted-foreground mb-1">****{account.mask}</div>
            <div className="text-sm font-medium text-foreground mb-2">{account.name}</div>
            <div className="text-2xl font-bold text-foreground">{formatCurrency(account.balance)}</div>
          </div>
          {account.utilization !== undefined && (
            <div className="text-right">
              <div className="text-xs text-muted-foreground mb-1">Utilization</div>
              <div
                className={`text-sm font-semibold ${
                  account.utilization >= 80
                    ? "text-red-600"
                    : account.utilization >= 50
                    ? "text-yellow-600"
                    : "text-green-600"
                }`}
              >
                {formatPercentage(account.utilization)}
              </div>
              {account.limit && (
                <div className="text-xs text-muted-foreground mt-1">
                  {formatCurrency(account.available || 0)} available
                </div>
              )}
            </div>
          )}
        </div>
        {account.limit && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Credit Limit</span>
              <span>{formatCurrency(account.limit)}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
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
        <Icon className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-semibold text-foreground">{title}</h2>
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
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="text-center">Loading overview...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">Error: {error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!overview) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground text-center">No overview data available.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const { summary, accounts, health } = overview.data

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-foreground">Financial Overview</h1>
        <p className="text-muted-foreground">
          Your complete financial snapshot at a glance
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card className="border border-gray-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Net Worth
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{formatCurrency(summary.net_worth)}</div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Total Savings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{formatCurrency(summary.total_savings)}</div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Credit Debt
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{formatCurrency(summary.total_credit_debt)}</div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Available Credit
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{formatCurrency(summary.available_credit)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Accounts Sections */}
      <div className="space-y-8 mb-8">
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
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl">Financial Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <div className="text-sm text-muted-foreground mb-2">Overall Status</div>
              <HealthBadge status={health.overall} />
            </div>

            <div>
              <div className="text-sm text-muted-foreground mb-2">Credit Utilization</div>
              <div
                className={`text-lg font-semibold ${
                  health.credit_utilization >= 80
                    ? "text-red-600"
                    : health.credit_utilization >= 50
                    ? "text-yellow-600"
                    : "text-green-600"
                }`}
              >
                {formatPercentage(health.credit_utilization)}
              </div>
            </div>

            {health.emergency_fund_months !== null && (
              <div>
                <div className="text-sm text-muted-foreground mb-2">Emergency Fund</div>
                <div className="text-lg font-semibold text-foreground">
                  {health.emergency_fund_months.toFixed(1)} months
                </div>
              </div>
            )}

            <div>
              <div className="text-sm text-muted-foreground mb-2">Cash Flow</div>
              <div
                className={`text-lg font-semibold ${
                  health.cash_flow_status === "negative"
                    ? "text-red-600"
                    : health.cash_flow_status === "tight"
                    ? "text-yellow-600"
                    : "text-green-600"
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
        </CardContent>
      </Card>
    </div>
  )
}

