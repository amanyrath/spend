import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { fetchInsights, type InsightsData } from "@/lib/api"
import { getValidUserId, formatCurrency, formatPercentage } from "@/lib/utils"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  ReferenceLine,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts"

// Color palette matching Trust Professional theme
const COLORS = {
  primary: "#1e40af",
  success: "#10b981",
  warning: "#f59e0b",
  error: "#ef4444",
  neutral: "#64748b",
}

const CHART_COLORS = [
  "#1e40af",
  "#3b82f6",
  "#60a5fa",
  "#93c5fd",
  "#bfdbfe",
  "#dbeafe",
]

export function InsightsPage() {
  const { userId } = useParams<{ userId: string }>()
  const [insights, setInsights] = useState<InsightsData | null>(null)
  const [period, setPeriod] = useState<"30d" | "90d">("30d")
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
    fetchInsights(validUserId, period)
      .then((data) => {
        setInsights(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [userId, period])

  const handlePeriodChange = (newPeriod: "30d" | "90d") => {
    setPeriod(newPeriod)
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="text-center">Loading insights...</div>
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

  if (!insights) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground text-center">No insights data available.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const { summary, charts } = insights.data

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2 text-foreground">Financial Insights</h1>
            <p className="text-muted-foreground">
              Visualize your spending patterns and financial habits
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant={period === "30d" ? "default" : "outline"}
              onClick={() => handlePeriodChange("30d")}
              className="min-w-[100px]"
            >
              30 Days
            </Button>
            <Button
              variant={period === "90d" ? "default" : "outline"}
              onClick={() => handlePeriodChange("90d")}
              className="min-w-[100px]"
            >
              90 Days
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card className="border shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Total Spending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{formatCurrency(summary.total_spending)}</div>
          </CardContent>
        </Card>
        <Card className="border shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Average Daily Spend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{formatCurrency(summary.average_daily_spend)}</div>
          </CardContent>
        </Card>
        <Card className="border shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Top Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-foreground">{summary.top_category || "N/A"}</div>
          </CardContent>
        </Card>
        {summary.savings_rate !== null && (
          <Card className="border shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Savings Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-primary">{formatPercentage(summary.savings_rate)}</div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Chart 1: Spending by Category */}
      <Card className="mb-8 border shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl">Spending by Category</CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Breakdown of your expenses by category over the selected period
          </p>
        </CardHeader>
        <CardContent>
          {charts.spending_by_category.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No transaction data available for this period.
            </p>
          ) : (
                <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={charts.spending_by_category}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  type="number" 
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  dataKey="category" 
                  type="category" 
                  width={150}
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                />
                <Tooltip
                  formatter={(value: number, name: string, props: any) => [
                    `${formatCurrency(value)} (${props.payload.percentage}%)`,
                    "Amount",
                  ]}
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    padding: '8px'
                  }}
                />
                <Bar dataKey="amount" fill={COLORS.primary} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Chart 2: Credit Utilization Trend */}
      {charts.credit_utilization.length > 0 && (
        <Card className="mb-8 border shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl">Credit Utilization Trend</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Track your credit card utilization over time. Aim to stay below 30% for optimal credit health.
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart
                data={charts.credit_utilization}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="date" 
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  domain={[0, 100]} 
                  tickFormatter={(value) => `${value}%`}
                  stroke="#64748b"
                  style={{ fontSize: '12px' }}
                />
                <Tooltip
                  formatter={(value: number, name: string, props: any) => [
                    `${value.toFixed(1)}% utilization (${formatCurrency(props.payload.balance)} / ${formatCurrency(props.payload.limit)})`,
                    "Utilization",
                  ]}
                  labelFormatter={(label) => `Week of ${label}`}
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    padding: '8px'
                  }}
                />
                <ReferenceLine y={30} stroke={COLORS.success} strokeDasharray="3 3" label={{ value: "30% (Good)", position: "topRight", fill: COLORS.success }} />
                <ReferenceLine y={50} stroke={COLORS.warning} strokeDasharray="3 3" label={{ value: "50% (Warning)", position: "topRight", fill: COLORS.warning }} />
                <ReferenceLine y={80} stroke={COLORS.error} strokeDasharray="3 3" label={{ value: "80% (High Risk)", position: "topRight", fill: COLORS.error }} />
                <Line
                  type="monotone"
                  dataKey="utilization"
                  stroke={COLORS.primary}
                  strokeWidth={3}
                  dot={{ fill: COLORS.primary, r: 5 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Chart 3: Subscription Breakdown */}
      <Card className="border shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl">Subscription Breakdown</CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Your recurring monthly subscriptions and their costs
          </p>
        </CardHeader>
        <CardContent>
          {charts.subscriptions.subscriptions.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No subscriptions detected.
            </p>
          ) : (
            <div className="flex flex-col items-center">
              <div className="mb-6 text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">Total Monthly Recurring</div>
                <div className="text-3xl font-bold text-primary">{formatCurrency(charts.subscriptions.total_monthly)}</div>
              </div>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={charts.subscriptions.subscriptions}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ merchant, amount, percent }) =>
                      `${merchant}: ${formatCurrency(amount)} (${(percent * 100).toFixed(0)}%)`
                    }
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="amount"
                  >
                    {charts.subscriptions.subscriptions.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                        stroke="#fff"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '6px',
                      padding: '8px'
                    }}
                  />
                  <Legend
                    formatter={(value, entry: any) =>
                      `${entry.payload.merchant}: ${formatCurrency(entry.payload.amount)}`
                    }
                    wrapperStyle={{ fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
